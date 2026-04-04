class TextInteraction:
    """Adapter to reuse slash command handlers with text (prefix) commands."""

    def __init__(self, ctx):
        self.guild_id = ctx.guild.id if ctx.guild else None
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.user = ctx.author
        self.response = self
        self.voice_client = ctx.guild.voice_client if ctx.guild else None

    async def defer(self, **kwargs):
        pass

    class Followup:
        def __init__(self, channel):
            self.channel = channel

        async def send(self, content=None, file=None, embed=None):
            if file:
                await self.channel.send(content, file=file)
            elif embed:
                await self.channel.send(embed=embed)
            else:
                await self.channel.send(content)

    @property
    def followup(self):
        return self.Followup(self.channel)
