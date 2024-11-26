import nextcord
from nextcord.ext import commands

class Clean(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="clean")
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx, number: int):
        """Command to bulk delete messages."""
        deleted = await ctx.channel.purge(limit=number + 1)
        await ctx.send(f"Foram eliminadas {len(deleted) - 1} mensagens.", delete_after=3.5)

    @clean.error
    async def clean_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Por favor, indique o número de mensagens a apagar.", delete_after=3.5)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("Não tens permissões para apagar mensagens.", delete_after=3.5)
        else:
            await ctx.send("Ocorreu um erro ao executar o comando.", delete_after=3.5)

def setup(bot):
    bot.add_cog(Clean(bot))
