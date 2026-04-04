import logging
import time
import discord
import asyncio
from dataclasses import dataclass, field
from collections import deque
from utils.config import FFMPEG_OPTIONS, FFMPEG_PATH
from services.youtube import refresh_url
from services.database import log_play

log = logging.getLogger(__name__)

INACTIVITY_TIMEOUT = 300
HISTORY_LIMIT = 10


@dataclass
class GuildPlayer:
    queue: deque = field(default_factory=deque)
    current_track: dict | None = None
    play_event: asyncio.Event | None = None
    player_task: asyncio.Task | None = None
    inactivity_task: asyncio.Task | None = None
    seeking: bool = False
    loop_mode: str = 'off'
    history: list = field(default_factory=list)
    skip_history: bool = False
    active_np_message: int | None = None
    playback_start_time: float | None = None
    playback_offset: float = 0
    pause_time: float | None = None


_players: dict[int, GuildPlayer] = {}


def get_player(guild_id: int) -> GuildPlayer:
    if guild_id not in _players:
        _players[guild_id] = GuildPlayer()
    return _players[guild_id]


def get_current_track(guild_id: int) -> dict | None:
    p = _players.get(guild_id)
    return p.current_track if p else None


def get_queue(guild_id: int) -> deque:
    return get_player(guild_id).queue


def get_active_np_message(guild_id: int) -> int | None:
    p = _players.get(guild_id)
    return p.active_np_message if p else None


def _notify_redis(guild_id):
    from services.message_bus import notify_state
    notify_state(guild_id)


def get_elapsed(guild_id):
    p = _players.get(guild_id)
    if not p or p.playback_start_time is None:
        return 0
    if p.pause_time is not None:
        return p.playback_offset + (p.pause_time - p.playback_start_time)
    return p.playback_offset + (time.time() - p.playback_start_time)


def pause_playback(guild_id):
    get_player(guild_id).pause_time = time.time()


def resume_playback(guild_id):
    p = get_player(guild_id)
    if p.pause_time is not None:
        paused_elapsed = p.pause_time - (p.playback_start_time or p.pause_time)
        p.playback_offset += paused_elapsed
        p.playback_start_time = time.time()
        p.pause_time = None


def parse_time(time_str):
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) != 2:
                raise ValueError
            mins, secs = int(parts[0]), int(parts[1])
            if mins < 0 or secs < 0 or secs >= 60:
                raise ValueError
            return mins * 60 + secs
        val = int(time_str)
        if val < 0:
            raise ValueError
        return val
    except (ValueError, TypeError):
        raise ValueError(f"Invalid time format: {time_str}")


def _format_duration(seconds):
    if not seconds:
        return None
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}:{secs:02d}"


def build_now_playing_embed(track, guild_id=None):
    embed = discord.Embed(title=track['title'], color=discord.Color.blue())

    duration = track.get('duration')
    elapsed = None
    if guild_id:
        p = _players.get(guild_id)
        if p and p.playback_start_time is not None:
            elapsed = get_elapsed(guild_id)

    if duration:
        dur_str = _format_duration(duration)
        if elapsed is not None:
            elapsed = min(elapsed, duration)
            el_str = _format_duration(elapsed)
            total = int(duration)
            pos = int(elapsed)
            bar_len = 12
            filled = round(pos / total * bar_len) if total > 0 else 0
            bar = '━' * filled + '●' + '─' * (bar_len - filled)
            embed.add_field(name="Progress", value=f"`{el_str}` {bar} `{dur_str}`", inline=False)
        else:
            embed.add_field(name="Duration", value=dur_str, inline=True)

    if track.get('webpage_url'):
        embed.add_field(name="Source", value=f"[YouTube]({track['webpage_url']})", inline=True)
    if track.get('thumbnail'):
        embed.set_thumbnail(url=track['thumbnail'])
    return embed


async def _create_source(track):
    url = track['url']
    for attempt in range(2):
        try:
            return discord.FFmpegPCMAudio(
                url, **FFMPEG_OPTIONS, executable=FFMPEG_PATH
            )
        except Exception as e:
            log.warning("FFmpegPCMAudio attempt %d failed: %s", attempt + 1, e)
            if attempt == 0 and 'webpage_url' in track:
                new_url = await refresh_url(track['webpage_url'])
                if new_url:
                    track['url'] = new_url
                    url = new_url
                    continue
    return None


async def start_player(voice_client, track, guild_id, channel):
    p = get_player(guild_id)
    if p.player_task and not p.player_task.done():
        add_to_queue(guild_id, track)
        return

    _cancel_inactivity_timer(guild_id)
    p.player_task = asyncio.create_task(
        _player_loop(voice_client, track, guild_id, channel)
    )


async def _player_loop(voice_client, first_track, guild_id, channel):
    p = get_player(guild_id)
    if not p.play_event:
        p.play_event = asyncio.Event()
    event = p.play_event
    loop = asyncio.get_running_loop()
    track = first_track

    try:
        while track:
            source = await _create_source(track)
            if not source:
                log.warning("Failed to create source for: %s", track.get('title'))
                track = _next_track(guild_id)
                continue

            p.current_track = track
            p.playback_start_time = time.time()
            p.playback_offset = 0
            p.pause_time = None
            event.clear()

            try:
                log_play(
                    guild_id,
                    track.get('requested_by', 0),
                    track['title'],
                    track.get('webpage_url')
                )
            except Exception:
                pass

            voice_client.play(
                source,
                after=lambda e, gid=guild_id, lp=loop: _on_track_end(e, gid, lp)
            )
            _notify_redis(guild_id)

            try:
                embed = build_now_playing_embed(track, guild_id)
                np_msg = await channel.send(embed=embed)
                p.active_np_message = np_msg.id
                await np_msg.add_reaction('❤️')
            except Exception:
                pass

            await event.wait()
            _notify_redis(guild_id)

            p.active_np_message = None
            p.playback_start_time = None
            p.playback_offset = 0
            p.pause_time = None

            if not voice_client.is_connected():
                break

            if p.loop_mode == 'track':
                pass
            else:
                if not p.skip_history:
                    p.history.append(track)
                    if len(p.history) > HISTORY_LIMIT:
                        p.history.pop(0)
                p.skip_history = False
                if p.loop_mode == 'queue':
                    add_to_queue(guild_id, track)
                track = _next_track(guild_id)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.error("Player loop error for guild %s: %s", guild_id, e)
    finally:
        p.current_track = None
        p.player_task = None
        p.playback_start_time = None
        p.playback_offset = 0
        p.pause_time = None
        if voice_client.is_connected():
            _start_inactivity_timer(voice_client, guild_id)


def _on_track_end(error, guild_id, loop):
    if error:
        log.error("Player error: %s", error)
    p = _players.get(guild_id)
    if p and p.seeking:
        return
    if p and p.play_event:
        loop.call_soon_threadsafe(p.play_event.set)


async def seek_track(voice_client, guild_id, pos_sec):
    p = _players.get(guild_id)
    if not p or not p.current_track:
        return False

    track = p.current_track
    url = track['url']
    if 'webpage_url' in track:
        new_url = await refresh_url(track['webpage_url'])
        if new_url:
            track['url'] = new_url
            url = new_url

    try:
        source = discord.FFmpegPCMAudio(
            url,
            before_options=f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 2000000 -probesize 524288 -ss {pos_sec}",
            options="-vn -ar 48000 -ac 2 -bufsize 256k",
            executable=FFMPEG_PATH
        )
    except Exception:
        return False

    loop = asyncio.get_running_loop()
    p.seeking = True
    voice_client.stop()
    await asyncio.sleep(0.05)
    p.seeking = False

    p.playback_start_time = time.time()
    p.playback_offset = pos_sec
    p.pause_time = None

    voice_client.play(
        source,
        after=lambda e, gid=guild_id, lp=loop: _on_track_end(e, gid, lp)
    )
    _notify_redis(guild_id)
    return True


def _next_track(guild_id):
    p = _players.get(guild_id)
    if p and p.queue:
        return p.queue.popleft()
    return None


def add_to_queue(guild_id, track):
    get_player(guild_id).queue.append(track)
    _notify_redis(guild_id)


def clear_queue_only(guild_id):
    p = _players.get(guild_id)
    if p:
        p.queue.clear()
    _notify_redis(guild_id)


def skip_to_position(guild_id, position):
    p = _players.get(guild_id)
    if not p or not p.queue:
        return 0
    position = min(position, len(p.queue))
    if position > 1:
        for _ in range(position - 1):
            p.queue.popleft()
    return position


def clear_queue(guild_id):
    p = _players.get(guild_id)
    if not p:
        return
    p.queue.clear()
    p.current_track = None
    p.seeking = False
    p.loop_mode = 'off'
    p.history.clear()
    p.skip_history = False
    p.active_np_message = None
    p.playback_start_time = None
    p.playback_offset = 0
    p.pause_time = None
    if p.player_task:
        p.player_task.cancel()
        p.player_task = None
    if p.play_event:
        p.play_event.set()
        p.play_event = None
    _cancel_inactivity_timer(guild_id)
    _notify_redis(guild_id)


def cycle_loop_mode(guild_id):
    p = get_player(guild_id)
    modes = ['off', 'track', 'queue']
    p.loop_mode = modes[(modes.index(p.loop_mode) + 1) % 3]
    _notify_redis(guild_id)
    return p.loop_mode


def pop_history(guild_id):
    p = _players.get(guild_id)
    if p and p.history:
        return p.history.pop()
    return None


def skip_history_once(guild_id):
    get_player(guild_id).skip_history = True


def _cancel_inactivity_timer(guild_id):
    p = _players.get(guild_id)
    if p and p.inactivity_task:
        p.inactivity_task.cancel()
        p.inactivity_task = None


def _start_inactivity_timer(voice_client, guild_id):
    _cancel_inactivity_timer(guild_id)
    p = get_player(guild_id)
    p.inactivity_task = asyncio.create_task(
        _inactivity_disconnect(voice_client, guild_id)
    )


async def _inactivity_disconnect(voice_client, guild_id):
    try:
        await asyncio.sleep(INACTIVITY_TIMEOUT)
        if voice_client.is_connected() and not voice_client.is_playing() and not voice_client.is_paused():
            await voice_client.disconnect()
            log.info("Disconnected from guild %s due to inactivity", guild_id)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass
    finally:
        p = _players.get(guild_id)
        if p:
            p.inactivity_task = None
