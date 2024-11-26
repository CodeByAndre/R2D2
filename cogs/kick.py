import nextcord
from nextcord.ext import commands

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="kick", description="Expulsa um membro do servidor.")
    async def kick(self, interaction: nextcord.Interaction, member: nextcord.Member, motivo: str = None):
        """Kicks a member from the server."""
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ Não tens permissão para usar este comando.", ephemeral=True)
            return

        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message("❌ Não tenho permissão para expulsar membros.", ephemeral=True)
            return

        try:
            await member.kick(reason=motivo)
            motivo = motivo if motivo else "Nenhum motivo fornecido."
            await interaction.response.send_message(f"✅ {member.mention} foi expulso/a do servidor.\nMotivo: {motivo}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu um erro ao tentar expulsar o membro: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Kick(bot))
