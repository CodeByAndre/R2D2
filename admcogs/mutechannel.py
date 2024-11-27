import nextcord
from nextcord.ext import commands

class MuteChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock_channel(self, ctx):
        """Lock the current channel by preventing users from sending messages."""
        if ctx.author.id != 516735882259333132 and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Apenas os administradores podem usar este comando.")
            return

        channel = ctx.channel

        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send("🔒 Todos os usuários foram bloqueados de falar neste canal.")
        except Exception as e:
            await ctx.send(f"❌ Ocorreu um erro ao tentar bloquear o canal: {e}")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock_channel(self, ctx):
        """Unlock the current channel by allowing users to send messages."""
        if ctx.author.id != 516735882259333132 and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Apenas os administradores podem usar este comando.")
            return

        channel = ctx.channel

        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            await ctx.send("🔓 Todos os usuários foram desbloqueados para falar neste canal.")
        except Exception as e:
            await ctx.send(f"❌ Ocorreu um erro ao tentar desbloquear o canal: {e}")

    @lock_channel.error
    async def lock_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Não tens permissão para usar este comando.")
        else:
            await ctx.send("❌ Ocorreu um erro ao tentar bloquear o canal.")

    @unlock_channel.error
    async def unlock_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Não tens permissão para usar este comando.")
        else:
            await ctx.send("❌ Ocorreu um erro ao tentar desbloquear o canal.")

def setup(bot):
    bot.add_cog(MuteChannel(bot))
