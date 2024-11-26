import nextcord
from nextcord.ext import commands

class SlowMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    async def set_slowmode(self, ctx, seconds: int):
        """Sets the slowmode in the current channel."""
        try:
            # Set the slowmode delay for the current channel
            await ctx.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                await ctx.send("🛑 Modo lento desativado neste canal.")
            else:
                await ctx.send(f"🐌 Modo lento ativado! Os usuários devem esperar **{seconds} segundos** antes de enviar uma nova mensagem.")
        except Exception as e:
            await ctx.send(f"❌ Ocorreu um erro ao tentar definir o modo lento: {e}")

    @set_slowmode.error
    async def slowmode_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Não tens permissão para usar este comando.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Por favor, insere um número válido de segundos para o modo lento.")
        else:
            await ctx.send("❌ Ocorreu um erro ao tentar definir o modo lento.")

def setup(bot):
    bot.add_cog(SlowMode(bot))
