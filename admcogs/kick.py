import nextcord
from nextcord.ext import commands
import logging

logger = logging.getLogger("DiscordBot")

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="kick", description="Kick um membro.")
    async def kick(self, interaction: nextcord.Interaction, member: nextcord.Member, motivo: str = None):
        if interaction.user.id != 516735882259333132 and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas os administradores podem usar este comando.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ Não tens permissão para usar este comando.", ephemeral=True)
            return

        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.response.send_message("❌ Não tenho permissão para expulsar membros.", ephemeral=True)
            return

        try:
            await member.kick(reason=motivo)
            motivo = motivo if motivo else "Nenhum motivo fornecido."
            logger.info(f"Slash command 'kick' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name} para expulsar {member} com motivo: {motivo}")
            await interaction.response.send_message(f"✅ {member.mention} foi expulso/a do servidor.\nMotivo: {motivo}")
        except Exception as e:
            logger.error(f"Erro no comando 'kick' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {e}")
            await interaction.response.send_message(f"❌ Ocorreu um erro ao tentar expulsar o membro: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Kick(bot))
