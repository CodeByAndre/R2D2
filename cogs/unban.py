import nextcord
from nextcord.ext import commands

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="unban", description="Desbane um utilizador do servidor pelo ID.")
    async def unban(
        self,
        interaction: nextcord.Interaction,
        user_id: str = nextcord.SlashOption(description="ID do utilizador para desbanir", required=True),
    ):
        """Unbans a user from the server using their ID."""
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"{user} foi desbanido/a do servidor.", ephemeral=True)
        except nextcord.NotFound:
            await interaction.response.send_message("❌ Utilizador não encontrado. Verifica o ID.", ephemeral=True)
        except nextcord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissões para desbanir este utilizador.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu um erro: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Unban(bot))
