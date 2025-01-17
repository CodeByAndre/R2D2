import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import logging

logger = logging.getLogger("DiscordBot")

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ban", description="Da ban a um membro.")
    async def ban(self, interaction: Interaction, member: nextcord.Member, reason: str = "Sem razão"):
        if interaction.user.id != 516735882259333132 and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas os administradores podem usar este comando.", ephemeral=True)
            return

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ Não tens permissões para usar este comando.", ephemeral=True)
            return

        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("❌ Eu não tenho permissões para banir membros.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            logger.info(f"Slash command 'ban' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name} para banir {member} com razão: {reason}")
            await interaction.response.send_message(f"✅ {member} foi banido/a do servidor. Razão: {reason}")
        except Exception as e:
            logger.error(f"Erro no comando 'ban' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {e}")
            await interaction.response.send_message(f"❌ Ocorreu um erro ao tentar banir: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Ban(bot))
