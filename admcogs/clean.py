import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import logging

logger = logging.getLogger("DiscordBot")

class Clean(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="clean", description="Bulk delete messages from the current channel.")
    async def clean(self, interaction: Interaction, number: int):
        logger.info(
            f"Slash command 'clean' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}"
        )

        if interaction.user.id != 516735882259333132 and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas os administradores podem usar este comando.",
                ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Não tens permissões para apagar mensagens.", ephemeral=True)
            return

        if number <= 0:
            await interaction.response.send_message("❌ Por favor, insira um número maior que 0.", ephemeral=True)
            return

        try:
            deleted = await interaction.channel.purge(limit=number)
            await interaction.response.send_message(f"✅ Foram eliminadas {len(deleted)} mensagens.", delete_after=3.5)
        except Exception as e:
            logger.error(
                f"Error in slash command 'clean' invoked by {interaction.user} in {interaction.guild.name}#{interaction.channel.name}: {e}"
            )
            await interaction.response.send_message(f"❌ Ocorreu um erro ao apagar mensagens: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Clean(bot))
