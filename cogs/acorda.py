import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import asyncio
import logging

logger = logging.getLogger("DiscordBot")

class Acordar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="acordar", description="Move uma pessoa entre canais para acordá-la.")
    async def acordar(self, interaction: Interaction, member: nextcord.Member):
        try:
            logger.info(f"Comando 'acordar' chamado por {interaction.user} no servidor {interaction.guild.name}")

            if interaction.user.id != 516735882259333132 and not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ Apenas administradores ou o usuário autorizado podem usar este comando.", ephemeral=True)
                logger.warning(f"{interaction.user} tentou usar 'acordar' sem permissão.")
                return

            if not interaction.user.voice:
                await interaction.response.send_message("❌ Precisas de estar em um canal de voz para usar este comando.", ephemeral=True)
                logger.warning(f"{interaction.user} tentou usar 'acordar' sem estar em um canal de voz.")
                return
            author_channel = interaction.user.voice.channel

            if not member.voice:
                await interaction.response.send_message(f"❌ `{member}` não está em nenhum canal de voz.", ephemeral=True)
                logger.warning(f"{interaction.user} tentou usar 'acordar', mas `{member}` não está em um canal de voz.")
                return
            member_channel = member.voice.channel

            voice_channels = [
                vc for vc in interaction.guild.voice_channels
                if vc != author_channel and vc.permissions_for(member).view_channel
            ]
            if not voice_channels:
                await interaction.response.send_message("❌ Não há canais disponíveis que o membro pode ver.", ephemeral=True)
                logger.warning(f"{interaction.user} tentou usar 'acordar', mas não há canais que `{member}` possa acessar.")
                return

            await interaction.response.send_message(f"A ACORDAR ESTE BURRO `{member}`!")
            logger.info(f"Iniciando movimentação de `{member}` entre canais no servidor {interaction.guild.name}")

            if member_channel == author_channel:
                await member.move_to(voice_channels[0])
                logger.info(f"O`{member}` está a ser movido")

            while True:
                for vc in voice_channels:
                    if not member.voice:
                        await interaction.followup.send(f"`{member}` desconectou. Loop interrompido!")
                        logger.info(f"Loop interrompido: `{member}` desconectou do canal de voz.")
                        return

                    if member.voice.channel == author_channel:
                        await interaction.followup.send(f"`{member}` ACORDOU. FINALMENTE!")
                        return

                    await member.move_to(vc)
                    logger.info(f"Movendo `{member}` para o canal `{vc.name}`.")
                    await asyncio.sleep(0.8)

        except Exception as e:
            logger.error(f"Erro no comando 'acordar': {e}")
            await interaction.response.send_message(f"❌ Ocorreu um erro: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(Acordar(bot))
