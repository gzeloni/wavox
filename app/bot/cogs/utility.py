import logging
import os
import asyncio
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

from services.music import parse_time, get_current_track
from services.youtube import get_youtube_url
from services.spotify import get_spotify_track
from utils.audio import create_clip, download_audio, cleanup_temp_dir
from utils.config import SPOTIFY_PATTERNS, MAX_CLIP_LENGTH, MAX_FILE_SIZE
from bot.cogs.utils import TextInteraction

log = logging.getLogger(__name__)


class UtilityCog(commands.Cog):
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

    @discord.app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🏓 Pong! {round(self.bot.latency * 1000)}ms", ephemeral=True)

    @discord.app_commands.command(name="clip", description="clip a section of current song")
    @discord.app_commands.describe(start="Start time (seconds or mm:ss)", end="End time (seconds or mm:ss)")
    async def clip(self, interaction: discord.Interaction, start: str, end: str):
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client
        guild_id = interaction.guild_id

        if not voice_client or not voice_client.is_playing():
            return await interaction.followup.send("❌ Nothing playing")

        temp_dir = None
        try:
            start_sec = parse_time(start)
            end_sec = parse_time(end)

            if end_sec <= start_sec:
                return await interaction.followup.send("❌ End time must be after start time")

            if end_sec - start_sec > MAX_CLIP_LENGTH:
                return await interaction.followup.send(f"❌ Max clip length is {MAX_CLIP_LENGTH}s")

            if not get_current_track(guild_id):
                return await interaction.followup.send("❌ Cannot determine current song")

            playing_url = get_current_track(guild_id)['url']
            await interaction.followup.send("✂️ Processing clip...")

            output_path, temp_dir = await create_clip(playing_url, start_sec, end_sec)

            if not output_path:
                return await interaction.followup.send(f"❌ Failed to create clip: {temp_dir}")

            clip_duration = end_sec - start_sec
            file = discord.File(
                output_path, filename=f"clip_{clip_duration}s.mp3")
            await interaction.followup.send("✅ Here's your clip!", file=file)

        except ValueError as e:
            await interaction.followup.send(f"❌ {e}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
        finally:
            if temp_dir:
                cleanup_temp_dir(temp_dir)

    @discord.app_commands.command(name="download", description="Download current song or from URL/search")
    @discord.app_commands.describe(query="URL or search term (leave empty to download current song)")
    async def download_cmd(self, interaction: discord.Interaction, query: str = None):
        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild_id
        temp_dir = None

        try:
            if not query:
                voice_client = interaction.guild.voice_client
                if not voice_client or not voice_client.is_connected():
                    return await interaction.followup.send("❌ Not connected to a voice channel")

                if not get_current_track(guild_id):
                    return await interaction.followup.send("❌ Nothing playing")

                track = get_current_track(guild_id)
                url = track['url']
                title = track['title']
            else:
                spotify_track_match = SPOTIFY_PATTERNS['track'].match(query)

                if spotify_track_match:
                    track_id = spotify_track_match.group(1)
                    track_info = await get_spotify_track(track_id)

                    if not track_info:
                        return await interaction.followup.send("❌ Failed to fetch track")

                    youtube_info = await get_youtube_url(track_info['search_query'])

                    if not youtube_info:
                        return await interaction.followup.send("❌ Couldn't find track")

                    url = youtube_info['url']
                    title = track_info['title']
                else:
                    youtube_info = await get_youtube_url(query)

                    if not youtube_info:
                        return await interaction.followup.send("❌ Nothing found")

                    url = youtube_info['url']
                    title = youtube_info['title']

            await interaction.followup.send("⏳ Downloading...")

            output_path, temp_dir = await download_audio(url, title)

            if not output_path:
                return await interaction.followup.send(f"❌ Failed: {temp_dir}")

            file_size = os.path.getsize(output_path)
            if file_size > MAX_FILE_SIZE:
                return await interaction.followup.send("❌ File too large (>8MB)")

            filename = f"{title.replace(' ', '_')[:40]}.mp3"
            file = discord.File(output_path, filename=filename)

            await interaction.followup.send(f"✅ Download complete ({file_size/1024/1024:.1f}MB)", file=file)
        except ValueError as e:
            await interaction.followup.send(f"❌ {e}")
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {str(e)}")
        finally:
            if temp_dir:
                cleanup_temp_dir(temp_dir)

    @discord.app_commands.command(name="lyrics", description="Show lyrics for current or searched song")
    @discord.app_commands.describe(query="Song name (leave empty for current track)")
    async def lyrics(self, interaction: discord.Interaction, query: str = None):
        await interaction.response.defer(ephemeral=True)

        if not query:
            track = get_current_track(interaction.guild_id)
            if not track:
                return await interaction.followup.send("❌ Nothing playing and no query provided")
            query = track['title']

        # Clean common suffixes from track titles
        for suffix in ['(Official Audio)', '(Official Video)', '(Lyrics)',
                       '(Official Music Video)', '[Official Audio]', '[Official Video]',
                       '(Audio)', '(Video)', '- Topic']:
            query = query.replace(suffix, '')
        query = query.strip()

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://lrclib.net/api/search?q={query}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ Lyrics service unavailable")
                    results = await resp.json()

            if not results:
                return await interaction.followup.send(f"❌ No lyrics found for: **{query}**")

            best = results[0]
            text = best.get('plainLyrics') or best.get('syncedLyrics', '')

            if not text:
                return await interaction.followup.send(f"❌ No lyrics found for: **{query}**")

            # Strip synced timestamps if present
            lines = []
            for line in text.split('\n'):
                if line.startswith('[') and ']' in line:
                    line = line[line.index(']') + 1:]
                lines.append(line)
            text = '\n'.join(lines).strip()

            artist = best.get('artistName', '')
            title = best.get('trackName', query)
            header = f"**{artist} — {title}**" if artist else f"**{title}**"

            # Discord embed description limit is 4096 chars
            if len(text) + len(header) + 2 > 4096:
                text = text[:4096 - len(header) - 20] + '\n\n*(...truncated)*'

            embed = discord.Embed(
                description=f"{header}\n\n{text}",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            await interaction.followup.send("❌ Lyrics search timed out")
        except Exception as e:
            log.error("Lyrics error: %s", e)
            await interaction.followup.send("❌ Failed to fetch lyrics")

    # --- Text command aliases ---

    @commands.command(name="ping")
    async def ping_text(self, ctx):
        await self.ping(TextInteraction(ctx))

    @commands.command(name="clip")
    async def cut_text(self, ctx, start: str, end: str):
        await self.clip(TextInteraction(ctx), start, end)

    @commands.command(name="download")
    async def download_text(self, ctx, *, query: str = None):
        await self.download_cmd(TextInteraction(ctx), query)

    @commands.command(name="lyrics")
    async def lyrics_text(self, ctx, *, query: str = None):
        await self.lyrics(TextInteraction(ctx), query)


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
