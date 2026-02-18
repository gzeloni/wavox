import discord
from discord.ext import commands
from utils.config import CMD_PREFIX, FFMPEG_PATH


def create_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(command_prefix=CMD_PREFIX, intents=intents)
    discord.FFmpegOpusAudio.ffmpeg_executable = FFMPEG_PATH

    @bot.event
    async def on_ready():
        try:
            await bot.tree.sync()
            print(f'✅ Bot ready as {bot.user}')
        except Exception as e:
            print(f'❌ Error syncing slash commands: {e}')

    @bot.event
    async def on_voice_state_update(member, before, after):
        if member == bot.user and before.channel is not None and after.channel is None:
            from services.music import clear_queue
            if before.channel.guild:
                clear_queue(before.channel.guild.id)
                print(
                    f"🧹 Cleaned up queue for guild {before.channel.guild.id}")

    @bot.event
    async def on_raw_reaction_add(payload):
        if payload.user_id == bot.user.id:
            return
        if str(payload.emoji) != '❤️':
            return
        from services.music import _active_np_messages, current_tracks
        from services.database import log_event
        guild_id = payload.guild_id
        if not guild_id:
            return
        if _active_np_messages.get(guild_id) != payload.message_id:
            return
        track = current_tracks.get(guild_id)
        if not track:
            return
        try:
            log_event(guild_id, payload.user_id, 'like', track['title'])
        except Exception:
            pass

    @bot.event
    async def on_raw_reaction_remove(payload):
        if payload.user_id == bot.user.id:
            return
        if str(payload.emoji) != '❤️':
            return
        from services.music import _active_np_messages, current_tracks
        from services.database import log_event
        guild_id = payload.guild_id
        if not guild_id:
            return
        if _active_np_messages.get(guild_id) != payload.message_id:
            return
        track = current_tracks.get(guild_id)
        if not track:
            return
        try:
            log_event(guild_id, payload.user_id, 'unlike', track['title'])
        except Exception:
            pass

    from bot.commands import register_commands
    register_commands(bot)

    return bot
