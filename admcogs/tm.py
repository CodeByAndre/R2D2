import os
import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

class Terminal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 516735882259333132

    @commands.command(name="tm")
    async def terminal_command(
        self,
        interaction: Interaction,
        command: str = SlashOption(description="The terminal command to run", required=True)
    ):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Apenas o dono pode usar este comando.", ephemeral=True, delete_after=2)
            return

        try:
            await interaction.response.send_message(f"🔄 Executando: `{command}`", ephemeral=True, delete_after=2)

            stream = os.popen(command)
            output = stream.read()

            if output:
                if len(output) > 2000:
                    await interaction.followup.send(
                        f"⚠️ Saída muito longa. Aqui estão os primeiros 2000 caracteres:\n```{output[:2000]}```",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(f"```{output}```", ephemeral=True, delete_after=15)
            else:
                await interaction.followup.send("✅ Comando executado com sucesso, mas sem saída.", ephemeral=True, delete_after=2)
        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao executar o comando: {e}", ephemeral=True, delete_after=2)

def setup(bot):
    bot.add_cog(Terminal(bot))
