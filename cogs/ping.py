from nextcord.ext import commands

class Ping(commands.Cog):
    """Comandos gerais do bot."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Responde com o ping do bot."""
        await ctx.send(f"Pong! Latência: {round(self.bot.latency * 1000)}ms")

def setup(bot):
    bot.add_cog(Ping(bot))
