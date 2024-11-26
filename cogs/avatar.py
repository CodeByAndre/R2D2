import nextcord
from nextcord.ext import commands
from nextcord import Interaction

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="avatar", description="Fetch and display the avatar of a user.")
    async def avatar(self, interaction: Interaction, member: nextcord.Member = None):
        """Fetches and displays the avatar of a user."""
        member = member or interaction.user

        embed = nextcord.Embed(
            title=f"Avatar de {member}",
            description=f"[Clica para baixar]({member.display_avatar.url})",
            colour=nextcord.Color.random()
        )
        embed.set_image(url=member.display_avatar.url)

        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Avatar(bot))
