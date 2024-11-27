import nextcord
from nextcord.ext import commands
from nextcord import Interaction

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="ban", description="Ban a member from the server.")
    async def ban(self, interaction: Interaction, member: nextcord.Member, reason: str = "Sem razão"):
        """Bans a member from the server."""
        if interaction.user.id != 516735882259333132 and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas os administradores podem usar este comando.",
                ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ Não tens permissões para usar este comando.", ephemeral=True)
            return

        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.response.send_message("❌ Eu não tenho permissões para banir membros.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"✅ {member} foi banido/a do servidor. Razão: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu um erro ao tentar banir: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Ban(bot))
