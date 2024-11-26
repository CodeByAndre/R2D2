import nextcord
from nextcord.ext import commands

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: nextcord.Member, *, motivo=None):
        """Kicks a member from the server."""
        if ctx.guild.me.guild_permissions.kick_members:
            await member.kick(reason=motivo)
            await ctx.send(f"{member} foi expulso/a do servidor. Motivo: {motivo if motivo else 'Nenhum motivo fornecido.'}")
        else:
            await ctx.send("Não tenho permissão para expulsar membros.")

    @kick.error
    async def kick_error(self, ctx, error):
        """Handles errors for the kick command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Não tens permissão para usar este comando.")

def setup(bot):
    bot.add_cog(Kick(bot))
