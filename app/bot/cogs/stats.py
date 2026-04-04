import logging
import discord
from discord.ext import commands
from discord import app_commands

from services.database import get_recent, get_top_tracks, get_most_active, get_user_status
from bot.cogs.utils import TextInteraction

log = logging.getLogger(__name__)


class StatsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction, error):
        log.error("Command /%s error: %s", interaction.command.name, error)
        msg = "❌ Something went wrong"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception:
            pass

    @discord.app_commands.command(name="recent", description="Show recently played tracks")
    async def recent(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rows = get_recent(interaction.guild_id)
        if not rows:
            return await interaction.followup.send("📋 No play history yet")

        embed = discord.Embed(title="🕐 Recently Played", color=discord.Color.blue())
        for row in rows:
            user_tag = f"<@{row['user_id']}>" if row['user_id'] else "Unknown"
            played = row['played_at'][:16].replace('T', ' ')
            embed.add_field(
                name=row['track_title'][:100],
                value=f"{user_tag} — {played}",
                inline=False
            )
        await interaction.followup.send(embed=embed)

    @discord.app_commands.command(name="toptracks", description="Show most played tracks")
    async def toptracks(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rows = get_top_tracks(interaction.guild_id)
        if not rows:
            return await interaction.followup.send("📋 No play history yet")

        embed = discord.Embed(title="🏆 Top Tracks", color=discord.Color.gold())
        for i, row in enumerate(rows, 1):
            embed.add_field(
                name=f"{i}. {row['track_title'][:100]}",
                value=f"**{row['plays']}** plays",
                inline=False
            )
        await interaction.followup.send(embed=embed)

    @discord.app_commands.command(name="mostplayed", description="Show users who played the most")
    async def mostplayed(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        rows = get_most_active(interaction.guild_id)
        if not rows:
            return await interaction.followup.send("📋 No play history yet")

        embed = discord.Embed(title="🎧 Most Active DJs", color=discord.Color.purple())
        for i, row in enumerate(rows, 1):
            user_tag = f"<@{row['user_id']}>" if row['user_id'] else "Unknown"
            embed.add_field(
                name=f"{i}. {user_tag}",
                value=f"**{row['plays']}** tracks played",
                inline=False
            )
        await interaction.followup.send(embed=embed)

    @discord.app_commands.command(name="status", description="Your listening stats (last 30 days)")
    @discord.app_commands.describe(user="User to check (default: yourself)")
    async def status(self, interaction: discord.Interaction, user: discord.User = None):
        await interaction.response.defer(ephemeral=True)
        target = user or interaction.user
        data = get_user_status(interaction.guild_id, target.id)

        if not data:
            return await interaction.followup.send(f"📋 No listening data for <@{target.id}> in the last 30 days")

        embed = discord.Embed(
            title=f"📊 Music Status — {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="Overview",
            value=(
                f"**{data['total_plays']}** plays · "
                f"**{data['total_skips']}** skips · "
                f"**{data['total_likes']}** likes"
            ),
            inline=False
        )

        embed.add_field(name="Skip Rate", value=f"{data['skip_rate']:.1f}%", inline=True)
        embed.add_field(name="Like Rate", value=f"{data['like_rate']:.1f}%", inline=True)
        embed.add_field(name="Repeat Rate", value=f"{data['repeat_rate']:.1f}%", inline=True)

        if data['top_tracks']:
            tracks_text = '\n'.join(
                f"`{i}.` {row['track_title'][:45]} ({row['plays']}x)"
                for i, row in enumerate(data['top_tracks'], 1)
            )
            embed.add_field(name="Top Tracks", value=tracks_text, inline=False)

        if data['top_artists']:
            artists_text = '\n'.join(
                f"`{i}.` {row['artist'][:40]} ({row['plays']}x)"
                for i, row in enumerate(data['top_artists'], 1)
            )
            embed.add_field(name="Top Artists", value=artists_text, inline=False)

        labels = ['🌙 00-06', '🌅 06-12', '☀️ 12-18', '🌆 18-24']
        blocks = data['hour_blocks']
        total_h = sum(blocks) or 1
        dist_lines = []
        for label, count in zip(labels, blocks):
            pct = count / total_h * 100
            bar_len = round(pct / 10)
            bar = '█' * bar_len + '░' * (10 - bar_len)
            dist_lines.append(f"{label} {bar} {pct:.0f}%")
        embed.add_field(name="Listening Hours", value='\n'.join(dist_lines), inline=False)

        await interaction.followup.send(embed=embed)

    # --- Text command aliases ---

    @commands.command(name="recent")
    async def recent_text(self, ctx):
        await self.recent(TextInteraction(ctx))

    @commands.command(name="toptracks")
    async def toptracks_text(self, ctx):
        await self.toptracks(TextInteraction(ctx))

    @commands.command(name="mostplayed")
    async def mostplayed_text(self, ctx):
        await self.mostplayed(TextInteraction(ctx))

    @commands.command(name="status")
    async def status_text(self, ctx, user: discord.User = None):
        await self.status(TextInteraction(ctx), user)


async def setup(bot):
    await bot.add_cog(StatsCog(bot))
