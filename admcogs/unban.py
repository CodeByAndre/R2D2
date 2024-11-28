import nextcord
from nextcord.ext import commands
import logging

logger = logging.getLogger("DiscordBot")

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="unban", description="Unban a member of the server with the member ID.")
    async def unban(
        self,
        interaction: nextcord.Interaction,
        user_id: str = nextcord.SlashOption(description="ID do utilizador para desbanir", required=True),
    ):
        if interaction.user.id != 516735882259333132 and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas os administradores podem usar este comando.", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            logger.info(f"Slash command 'unban' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name} para desbanir {user}")
            await interaction.response.send_message(f"{user} foi desbanido/a do servidor.", ephemeral=True)
        except nextcord.NotFound:
            logger.error(f"Erro no comando 'unban': Utilizador com ID {user_id} não encontrado.")
            await interaction.response.send_message("❌ Utilizador não encontrado. Verifica o ID.", ephemeral=True)
        except nextcord.Forbidden:
            logger.error(f"Erro no comando 'unban': Permissões insuficientes para desbanir o utilizador com ID {user_id}.")
            await interaction.response.send_message("❌ Não tenho permissões para desbanir este utilizador.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando 'unban' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {e}")
            await interaction.response.send_message(f"❌ Ocorreu um erro: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Unban(bot))
