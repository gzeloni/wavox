import logging
import discord
from discord.ext import commands
from utils.config import CMD_PREFIX, FFMPEG_PATH

log = logging.getLogger(__name__)

COGS = [
    'bot.cogs.music',
    'bot.cogs.stats',
    'bot.cogs.utility',
]


def create_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(command_prefix=CMD_PREFIX, intents=intents)
    discord.FFmpegOpusAudio.ffmpeg_executable = FFMPEG_PATH

    @bot.event
    async def on_ready():
        if not hasattr(bot, '_synced'):
            try:
                from services.message_bus import init_bus, register_guild
                await init_bus(bot)
                for guild in bot.guilds:
                    await register_guild(guild.id)
                for cog in COGS:
                    await bot.load_extension(cog)
                await bot.tree.sync()
                bot._synced = True
                log.info("Bot ready as %s (%d guilds)", bot.user, len(bot.guilds))
            except Exception as e:
                log.error("Error during setup: %s", e)
        else:
            log.info("Bot reconnected as %s", bot.user)

    @bot.event
    async def on_guild_join(guild):
        from services.message_bus import register_guild
        await register_guild(guild.id)
        log.info("Joined guild %s (%s)", guild.name, guild.id)

    @bot.event
    async def on_guild_remove(guild):
        from services.message_bus import unregister_guild
        await unregister_guild(guild.id)
        log.info("Removed from guild %s (%s)", guild.name, guild.id)

    @bot.event
    async def on_voice_state_update(member, before, after):
        from services.music import clear_queue

        # bot saiu do canal
        if member == bot.user and before.channel and not after.channel:
            if before.channel.guild:
                clear_queue(before.channel.guild.id)
                from services.message_bus import unregister_guild
                import asyncio
                asyncio.create_task(unregister_guild(before.channel.guild.id))
                log.info("Cleaned up queue for guild %s", before.channel.guild.id)
            return

        # alguém saiu de um canal onde o bot está — verifica se ficou sozinho
        if before.channel and member != bot.user:
            voice_client = before.channel.guild.voice_client
            if voice_client and voice_client.channel == before.channel:
                if len(before.channel.members) == 1:
                    clear_queue(before.channel.guild.id)
                    await voice_client.disconnect()
                    log.info("Left empty channel in guild %s", before.channel.guild.id)

    def _handle_reaction(payload, event_type):
        if payload.user_id == bot.user.id:
            return None
        if str(payload.emoji) != '❤️':
            return None
        from services.music import get_active_np_message, get_current_track
        guild_id = payload.guild_id
        if not guild_id:
            return None
        if get_active_np_message(guild_id) != payload.message_id:
            return None
        track = get_current_track(guild_id)
        if not track:
            return None
        return guild_id, payload.user_id, event_type, track['title']

    @bot.event
    async def on_raw_reaction_add(payload):
        result = _handle_reaction(payload, 'like')
        if result:
            from services.database import log_event
            try:
                log_event(*result)
            except Exception:
                pass

    @bot.event
    async def on_raw_reaction_remove(payload):
        result = _handle_reaction(payload, 'unlike')
        if result:
            from services.database import log_event
            try:
                log_event(*result)
            except Exception:
                pass

    return bot
