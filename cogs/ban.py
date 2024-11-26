import nextcord
from nextcord.ext import commands

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: nextcord.Member, *, reason=None):
        """Bans a member from the server."""
        if ctx.guild.me.guild_permissions.ban_members:
            await member.ban(reason=reason)
            await ctx.send(f"{member} foi banido/a do servidor. Razão: {reason if reason else 'Sem razão.'}")
        else:
            await ctx.send("Eu não tenho permissões para banir membros.")

    @ban.error
    async def ban_error(self, ctx, error):
        """Handles errors for the ban command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Não tens permissões para usar este comando.")

def setup(bot):
    bot.add_cog(Ban(bot))
