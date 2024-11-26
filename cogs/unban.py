import nextcord
from nextcord.ext import commands

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user_id: int):
        """Unbans a user from the server using their ID."""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.send(f"{user} foi desbanido/a do servidor.")
        except nextcord.NotFound:
            await ctx.send("Utilizador não encontrado. Verifica o ID.")
        except nextcord.Forbidden:
            await ctx.send("Não tenho permissões para desbanir este utilizador.")
        except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")

    @unban.error
    async def unban_error(self, ctx, error):
        """Handles errors for the unban command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Não tens permissão para usar este comando.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Por favor, fornece o ID do utilizador que queres desbanir.")

def setup(bot):
    bot.add_cog(Unban(bot))
