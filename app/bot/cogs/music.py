import logging
import discord
import asyncio
import random
from collections import deque
from discord.ext import commands
from discord import app_commands

from services.music import (
    add_to_queue, start_player, clear_queue, clear_queue_only, parse_time,
    seek_track, skip_to_position, get_player, get_current_track, get_queue,
    cycle_loop_mode, pop_history, skip_history_once, build_now_playing_embed,
    _format_duration, pause_playback, resume_playback
)
from services.message_bus import notify_state as _notify_redis
from services.database import log_event
from services.youtube import get_youtube_url, search_youtube_fast, resolve_youtube_entry
from services.spotify import get_spotify_track, get_spotify_playlist, get_spotify_album, process_spotify_tracks
from utils.config import SPOTIFY_PATTERNS, MAX_QUEUE_DISPLAY
from bot.cogs.utils import TextInteraction

log = logging.getLogger(__name__)


_background_tasks = set()


async def _get_first_valid_track(tracks):
    for i, track in enumerate(tracks[:2]):
        info = await get_youtube_url(track['search_query'])
        if info:
            return {
                'url': info['url'],
                'title': track['title'],
                'webpage_url': info.get('webpage_url'),
                'duration': track.get('duration') or info.get('duration'),
                'thumbnail': track.get('thumbnail') or info.get('thumbnail'),
            }, tracks[i+1:]
    return None, []


async def _handle_spotify_collection(tracks, guild_id, channel, user_id=0):
    if not tracks:
        return None, "❌ Empty or invalid collection"

    song, remaining = await _get_first_valid_track(tracks)
    if not song:
        return None, "❌ Cannot find tracks"

    song['requested_by'] = user_id

    if remaining:
        task = asyncio.create_task(process_spotify_tracks(
            remaining, guild_id, channel, user_id))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    return song, f"✅ Found {len(tracks)} tracks"


async def _play_autocomplete(interaction: discord.Interaction, current: str):
    if not current or len(current) < 2:
        return []
    try:
        results = await search_youtube_fast(current, max_results=5)
        choices = []
        for r in results:
            title = r['title'][:80]
            url = r.get('webpage_url', '')
            if url:
                choices.append(app_commands.Choice(name=title, value=url))
        return choices
    except Exception:
        return []


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction, error):
        log.error("Command /%s error: %s", interaction.command.name, error)
        msg = "❌ Something went wrong"
        if isinstance(error, app_commands.CommandInvokeError) and isinstance(error.original, ValueError):
            msg = f"❌ {error.original}"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass

    @discord.app_commands.command(name="play", description="Play audio from URL or search")
    @discord.app_commands.describe(query="URL or search term")
    @discord.app_commands.autocomplete(query=_play_autocomplete)
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(ephemeral=True)

        if not interaction.user.voice:
            return await interaction.followup.send("❌ Join a voice channel first")

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if not voice_client:
            try:
                voice_client = await voice_channel.connect()
            except Exception:
                return await interaction.followup.send("❌ Connection error")
        elif voice_client.channel != voice_channel:
            try:
                await voice_client.move_to(voice_channel)
            except Exception:
                return await interaction.followup.send("❌ Cannot move to your channel")

        guild_id = interaction.guild_id

        song = None
        for pattern_type, pattern in SPOTIFY_PATTERNS.items():
            match = pattern.match(query)
            if match:
                item_id = match.group(1)

                if pattern_type == 'track':
                    track_info = await get_spotify_track(item_id)
                    if not track_info:
                        return await interaction.followup.send("❌ Failed to fetch track")

                    youtube_info = await get_youtube_url(track_info['search_query'])
                    if not youtube_info:
                        return await interaction.followup.send("❌ Couldn't find track")

                    song = {
                        'url': youtube_info['url'],
                        'title': track_info['title'],
                        'webpage_url': youtube_info.get('webpage_url'),
                        'duration': track_info.get('duration') or youtube_info.get('duration'),
                        'thumbnail': track_info.get('thumbnail') or youtube_info.get('thumbnail'),
                    }

                elif pattern_type == 'playlist':
                    tracks = await get_spotify_playlist(item_id)
                    if not tracks:
                        return await interaction.followup.send("❌ Failed to load playlist")
                    song, msg = await _handle_spotify_collection(tracks, guild_id, interaction.channel, interaction.user.id)
                    if not song:
                        return await interaction.followup.send(msg)
                    await interaction.followup.send(msg)

                elif pattern_type == 'album':
                    tracks = await get_spotify_album(item_id)
                    if not tracks:
                        return await interaction.followup.send("❌ Failed to load album")
                    song, msg = await _handle_spotify_collection(tracks, guild_id, interaction.channel, interaction.user.id)
                    if not song:
                        return await interaction.followup.send(msg)
                    await interaction.followup.send(msg)

                break

        if not song:
            is_url = query.startswith(('http://', 'https://'))

            if is_url:
                youtube_info = await resolve_youtube_entry(query)
                if not youtube_info:
                    return await interaction.followup.send("❌ Nothing found")
                song = youtube_info
            else:
                youtube_info = await get_youtube_url(query)
                if not youtube_info:
                    return await interaction.followup.send("❌ Nothing found")
                song = youtube_info

        song['requested_by'] = interaction.user.id

        if voice_client.is_playing() or voice_client.is_paused():
            add_to_queue(guild_id, song)
            await interaction.followup.send(f"✅ Added to queue: **{song['title']}**")
        else:
            await start_player(voice_client, song, guild_id, interaction.channel)
            await interaction.followup.send(f"🎵 Playing: **{song['title']}**")

    @discord.app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client

        if voice_client:
            clear_queue(interaction.guild_id)
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
            await voice_client.disconnect()
            await interaction.followup.send("⏹️ Stopped and cleared queue")
        else:
            await interaction.followup.send("❌ Not in a voice channel")

    @discord.app_commands.command(name="skip", description="Skip current or jump to queue position")
    @discord.app_commands.describe(position="Queue position to skip to (e.g. 3 = skip to 3rd in queue)")
    async def skip(self, interaction: discord.Interaction, position: int = None):
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild_id

        if not voice_client or (not voice_client.is_playing() and not voice_client.is_paused()):
            return await interaction.followup.send("❌ Nothing playing")

        track = get_current_track(guild_id)

        if position and position > 1:
            q = get_queue(guild_id)
            queue_len = len(q)
            if queue_len == 0:
                return await interaction.followup.send("❌ Queue is empty")
            if position > queue_len:
                return await interaction.followup.send(f"❌ Queue only has {queue_len} tracks")
            skipped = skip_to_position(guild_id, position)
            voice_client.stop()
            try:
                log_event(guild_id, interaction.user.id, 'skip', track['title'] if track else None)
            except Exception:
                pass
            await interaction.followup.send(f"⏭️ Skipped to position {position} ({skipped - 1} tracks removed)")
        else:
            voice_client.stop()
            try:
                log_event(guild_id, interaction.user.id, 'skip', track['title'] if track else None)
            except Exception:
                pass
            await interaction.followup.send("⏭️ Skipped")

    @discord.app_commands.command(name="clear", description="Clear the queue (keeps current track playing)")
    async def clear(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id
        q = get_queue(guild_id)
        if not q:
            return await interaction.followup.send("📋 Queue is already empty")
        count = len(q)
        clear_queue_only(guild_id)
        await interaction.followup.send(f"🗑️ Cleared {count} tracks from the queue")

    @discord.app_commands.command(name="queue", description="Show current queue")
    async def queue_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id
        q = get_queue(guild_id)

        if q:
            embed = discord.Embed(title="🎵 Queue", color=discord.Color.blue())

            for i, song in enumerate(list(q)[:MAX_QUEUE_DISPLAY], 1):
                name = "Next:" if i == 1 else f"{i}."
                value = f"**{song['title']}**" if i == 1 else song['title']
                embed.add_field(name=name, value=value, inline=False)

            remaining = len(q) - MAX_QUEUE_DISPLAY
            if remaining > 0:
                embed.add_field(
                    name="", value=f"*And {remaining} more...*", inline=False)

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("📋 Queue is empty")

    @discord.app_commands.command(name="pause", description="Pause playback")
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_playing():
            pause_playback(interaction.guild_id)
            voice_client.pause()
            _notify_redis(interaction.guild_id)
            await interaction.followup.send("⏸️ Paused")
        else:
            await interaction.followup.send("❌ Nothing playing")

    @discord.app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client

        if voice_client and voice_client.is_paused():
            resume_playback(interaction.guild_id)
            voice_client.resume()
            _notify_redis(interaction.guild_id)
            await interaction.followup.send("▶️ Resumed")
        else:
            await interaction.followup.send("❌ Nothing paused")

    @discord.app_commands.command(name="goto", description="Jump to position in song")
    @discord.app_commands.describe(position="Time position (seconds or mm:ss)")
    async def goto(self, interaction: discord.Interaction, position: str):
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild_id

        if voice_client and (voice_client.is_playing() or voice_client.is_paused()) and get_current_track(guild_id):
            pos_sec = parse_time(position)
            success = await seek_track(voice_client, guild_id, pos_sec)
            if success:
                await interaction.followup.send(f"▶️ Jumped to {position}")
            else:
                await interaction.followup.send("❌ goto failed")
        else:
            await interaction.followup.send("❌ Nothing playing")

    @discord.app_commands.command(name="loop", description="Cycle loop mode: off / track / queue")
    async def loop(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        mode = cycle_loop_mode(interaction.guild_id)
        labels = {'off': '➡️ Loop off', 'track': '🔂 Looping track', 'queue': '🔁 Looping queue'}
        await interaction.followup.send(labels[mode])

    @discord.app_commands.command(name="previous", description="Go back to the previous track")
    async def previous(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild_id

        if not voice_client or (not voice_client.is_playing() and not voice_client.is_paused()):
            return await interaction.followup.send("❌ Nothing playing")

        prev = pop_history(guild_id)
        if not prev:
            return await interaction.followup.send("❌ No previous track")

        get_queue(guild_id).appendleft(prev)
        skip_history_once(guild_id)
        voice_client.stop()
        await interaction.followup.send(f"⏮️ Going back to: **{prev['title']}**")

    @discord.app_commands.command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id
        q = get_queue(guild_id)

        if q:
            items = list(q)
            random.shuffle(items)
            q.clear()
            q.extend(items)
            await interaction.followup.send(f"🔀 Shuffled {len(q)} tracks")
        else:
            await interaction.followup.send("📋 Queue is empty")

    @discord.app_commands.command(name="nowplaying", description="Show current track info")
    async def nowplaying(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild_id
        track = get_current_track(guild_id)
        if not track:
            return await interaction.followup.send("❌ Nothing playing")
        embed = build_now_playing_embed(track, guild_id)
        await interaction.followup.send(embed=embed)

    # --- Text command aliases ---

    @commands.command(name="play")
    async def play_text(self, ctx, *, query: str):
        await self.play(TextInteraction(ctx), query)

    @commands.command(name="stop")
    async def stop_text(self, ctx):
        await self.stop(TextInteraction(ctx))

    @commands.command(name="skip")
    async def skip_text(self, ctx, position: int = None):
        await self.skip(TextInteraction(ctx), position)

    @commands.command(name="clear")
    async def clear_text(self, ctx):
        await self.clear(TextInteraction(ctx))

    @commands.command(name="queue")
    async def queue_text(self, ctx):
        await self.queue_cmd(TextInteraction(ctx))

    @commands.command(name="pause")
    async def pause_text(self, ctx):
        await self.pause(TextInteraction(ctx))

    @commands.command(name="resume")
    async def resume_text(self, ctx):
        await self.resume(TextInteraction(ctx))

    @commands.command(name="goto")
    async def seek_text(self, ctx, position: str):
        await self.goto(TextInteraction(ctx), position)

    @commands.command(name="loop")
    async def loop_text(self, ctx):
        await self.loop(TextInteraction(ctx))

    @commands.command(name="previous")
    async def previous_text(self, ctx):
        await self.previous(TextInteraction(ctx))

    @commands.command(name="shuffle")
    async def shuffle_text(self, ctx):
        await self.shuffle(TextInteraction(ctx))

    @commands.command(name="nowplaying")
    async def nowplaying_text(self, ctx):
        await self.nowplaying(TextInteraction(ctx))


async def setup(bot):
    await bot.add_cog(MusicCog(bot))
