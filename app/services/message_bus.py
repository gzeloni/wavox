import json
import asyncio
import logging
from os import getenv

import redis.asyncio as redis

log = logging.getLogger(__name__)

_bot = None
_redis = None
_state_queue: asyncio.Queue | None = None
_publisher_task = None
_consumer_task = None

REDIS_URL = getenv("REDIS_URL", "redis://redis:6379/0")


async def init_bus(bot):
    global _bot, _redis, _state_queue, _publisher_task, _consumer_task

    _bot = bot
    _redis = redis.from_url(REDIS_URL, decode_responses=True)
    _state_queue = asyncio.Queue(maxsize=256)

    _publisher_task = asyncio.create_task(_state_publisher())
    _consumer_task = asyncio.create_task(_command_consumer())
    log.info("Message bus connected (Redis pub/sub)")


async def close_bus():
    global _publisher_task, _consumer_task
    if _publisher_task:
        _publisher_task.cancel()
    if _consumer_task:
        _consumer_task.cancel()
    if _redis:
        await _redis.aclose()


def notify_state(guild_id):
    """Non-blocking. O(1). Safe to call from audio loop."""
    if _state_queue is None:
        return
    try:
        _state_queue.put_nowait(guild_id)
    except asyncio.QueueFull:
        pass


async def register_guild(guild_id):
    if _redis:
        try:
            await _redis.sadd("wavox:active_guilds", str(guild_id))
        except Exception:
            pass


async def unregister_guild(guild_id):
    if _redis:
        try:
            await _redis.srem("wavox:active_guilds", str(guild_id))
            await _redis.delete(f"wavox:guild:{guild_id}:state")
        except Exception:
            pass


# --- State publisher (dedicated task, never touches audio loop) ---

async def _state_publisher():
    while True:
        try:
            guild_id = await _state_queue.get()

            # Debounce: wait briefly then drain duplicates
            await asyncio.sleep(0.05)
            guilds = {guild_id}
            while not _state_queue.empty():
                try:
                    guilds.add(_state_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break

            for gid in guilds:
                try:
                    state = _build_state(gid)
                    payload = json.dumps({"type": "state_update", "data": state})

                    await _redis.publish(f"wavox:events:{gid}", payload)
                    await _redis.set(
                        f"wavox:guild:{gid}:state", payload, ex=300
                    )
                except Exception as e:
                    log.warning("State publish error for guild %s: %s", gid, e)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.error("State publisher error: %s", e)
            await asyncio.sleep(1)


def _build_state(guild_id):
    from services.music import get_player, _players

    p = _players.get(guild_id)
    state = {
        "now_playing": None,
        "queue": [],
        "is_playing": False,
        "is_paused": False,
        "loop_mode": p.loop_mode if p else "off",
    }

    if p and p.current_track:
        track = p.current_track
        voice_client = None
        for vc in _bot.voice_clients:
            if vc.guild.id == guild_id:
                voice_client = vc
                break

        state["now_playing"] = {
            "title": track.get("title"),
            "thumbnail": track.get("thumbnail"),
            "webpage_url": track.get("webpage_url"),
            "duration": track.get("duration"),
            "started_at": p.playback_start_time or 0,
            "offset": p.playback_offset,
            "paused_at": p.pause_time,
        }
        if voice_client:
            state["is_playing"] = voice_client.is_playing()
            state["is_paused"] = voice_client.is_paused()

    if p and p.queue:
        state["queue"] = [
            {"title": t.get("title"), "duration": t.get("duration")}
            for t in list(p.queue)
        ]

    return state


# --- Command consumer (Redis pub/sub) ---

async def _command_consumer():
    pubsub = _redis.pubsub()
    await pubsub.subscribe("wavox:commands")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                cmd = json.loads(message["data"])
                guild_id = int(cmd.pop("guild_id", 0))
                if guild_id:
                    await _handle_command(guild_id, cmd)
            except Exception as e:
                log.error("Command handler error: %s", e)
    except asyncio.CancelledError:
        raise
    finally:
        await pubsub.unsubscribe("wavox:commands")
        await pubsub.aclose()


async def _handle_command(guild_id, cmd):
    from collections import deque
    from services.music import (
        seek_track, pop_history, skip_history_once,
        get_player, get_queue, cycle_loop_mode, parse_time,
        clear_queue, clear_queue_only,
        pause_playback, resume_playback
    )
    import random

    action = cmd.get("action")

    if action == "get_user_status":
        await _handle_user_status(guild_id, cmd)
        return
    if action == "search":
        await _handle_search(guild_id, cmd)
        return

    voice_client = None
    for vc in _bot.voice_clients:
        if vc.guild.id == guild_id:
            voice_client = vc
            break

    if not voice_client:
        return

    if action == "pause":
        if voice_client.is_playing():
            pause_playback(guild_id)
            voice_client.pause()
    elif action == "resume":
        if voice_client.is_paused():
            resume_playback(guild_id)
            voice_client.resume()
    elif action == "skip":
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
    elif action == "previous":
        prev = pop_history(guild_id)
        if prev:
            q = get_queue(guild_id)
            q.appendleft(prev)
            skip_history_once(guild_id)
            voice_client.stop()
    elif action == "shuffle":
        q = get_queue(guild_id)
        if q:
            items = list(q)
            random.shuffle(items)
            q.clear()
            q.extend(items)
    elif action == "loop":
        cycle_loop_mode(guild_id)
    elif action == "goto":
        position = cmd.get("position", "0")
        pos_sec = parse_time(str(position))
        await seek_track(voice_client, guild_id, pos_sec)
    elif action == "stop":
        clear_queue(guild_id)
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        if voice_client.is_connected():
            await voice_client.disconnect()
    elif action == "clear":
        clear_queue_only(guild_id)
    elif action == "skip_to":
        from services.music import skip_to_position
        pos = int(cmd.get("position", 1))
        skip_to_position(guild_id, pos)
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
    elif action == "play":
        query = cmd.get("query", "")
        if query:
            await _handle_play(guild_id, voice_client, query, cmd.get("user_id", 0))

    notify_state(guild_id)


async def _handle_play(guild_id, voice_client, query, user_id):
    from services.youtube import get_youtube_url
    from services.music import add_to_queue, start_player

    info = await get_youtube_url(query)
    if not info:
        return

    info['requested_by'] = int(user_id) if user_id else 0

    if voice_client.is_playing() or voice_client.is_paused():
        add_to_queue(guild_id, info)
    else:
        guild = voice_client.guild
        channel = guild.system_channel or next(
            (ch for ch in guild.text_channels
             if ch.permissions_for(guild.me).send_messages), None
        )
        if channel:
            await start_player(voice_client, info, guild_id, channel)


async def _handle_user_status(guild_id, cmd):
    from services.database import get_user_status

    user_id = int(cmd.get("user_id", 0))
    request_id = cmd.get("request_id")
    if not request_id or not _redis:
        return

    data = get_user_status(guild_id, user_id)
    if data:
        result = {
            'total_plays': data['total_plays'],
            'total_skips': data['total_skips'],
            'total_likes': data['total_likes'],
            'skip_rate': round(data['skip_rate'], 1),
            'like_rate': round(data['like_rate'], 1),
            'repeat_rate': round(data['repeat_rate'], 1),
            'top_tracks': [
                {'title': r['track_title'], 'plays': r['plays']}
                for r in data['top_tracks']
            ],
            'top_artists': [
                {'artist': r['artist'], 'plays': r['plays']}
                for r in data['top_artists']
            ],
            'hour_blocks': data['hour_blocks'],
        }
    else:
        result = {}

    await _redis.lpush(f"wavox:response:{request_id}", json.dumps(result))
    await _redis.expire(f"wavox:response:{request_id}", 30)


async def _handle_search(guild_id, cmd):
    from services.youtube import search_youtube_fast

    query = cmd.get("query", "").strip()
    request_id = cmd.get("request_id")
    if not request_id or not _redis or not query:
        return

    results = await search_youtube_fast(query, max_results=6)

    items = []
    for r in results:
        url = r.get("webpage_url", "")
        source = "youtube"
        if "soundcloud.com" in url:
            source = "soundcloud"
        elif "spotify.com" in url:
            source = "spotify"
        items.append({
            "title": r.get("title", ""),
            "url": url,
            "duration": r.get("duration"),
            "channel": r.get("channel", ""),
            "source": source,
        })

    await _redis.lpush(f"wavox:response:{request_id}", json.dumps(items))
    await _redis.expire(f"wavox:response:{request_id}", 30)
