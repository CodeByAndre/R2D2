import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger("DiscordBot")

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="translate", description="Traduza o texto para o idioma especificado.")
    async def translate(
        self, 
        interaction: nextcord.Interaction, 
        lang: str = nextcord.SlashOption(description="Código do idioma para traduzir (ex: en, pt, es)", required=True),
        text: str = nextcord.SlashOption(description="Texto que deseja traduzir", required=True)
    ):
        try:
            translated = GoogleTranslator(source='auto', target=lang).translate(text)
            embed = nextcord.Embed(
                title=f"Tradução para {lang}",
                description=translated,
                color=nextcord.Color.blue()
            )
            embed.set_footer(text="Powered by Google Translator")
            logger.info(f"Slash command 'translate' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}. Texto traduzido para '{lang}': {text}")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Erro no comando 'translate' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {e}")
            await interaction.response.send_message(
                "❌ Desculpa, ocorreu um erro ao tentar traduzir o texto. Verifique o código do idioma e tente novamente.",
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(Translate(bot))
