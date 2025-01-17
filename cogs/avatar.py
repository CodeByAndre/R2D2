import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import logging

logger = logging.getLogger("DiscordBot")

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="avatar", description="Mostrar avatar de um utilizador.")
    async def avatar(self, interaction: Interaction, member: nextcord.Member = None):
        member = member or interaction.user

        try:
            embed = nextcord.Embed(
                title=f"Avatar de {member}",
                description=f"[Clica para baixar]({member.display_avatar.url})",
                colour=nextcord.Color.random()
            )
            embed.set_image(url=member.display_avatar.url)

            logger.info(f"Slash command 'avatar' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name} para obter o avatar de {member}")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando 'avatar' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {e}")
            await interaction.response.send_message(f"❌ Ocorreu um erro ao buscar o avatar: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Avatar(bot))
