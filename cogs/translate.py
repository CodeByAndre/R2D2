import nextcord
from nextcord.ext import commands
from deep_translator import GoogleTranslator

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="translate")
    async def translate(self, ctx, lang: str, *, text: str):
        """Translate the provided text to the specified language."""
        try:
            translated = GoogleTranslator(source='auto', target=lang).translate(text)
            embed = nextcord.Embed(
                title=f"Tradução para {lang}",
                description=translated,
                color=nextcord.Color.blue()
            )
            embed.set_footer(text="Powered by Google Translator")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(
                "❌ Desculpa, ocorreu um erro ao tentar traduzir o texto. Verifique o código do idioma e tente novamente."
            )

    @translate.error
    async def translate_error(self, ctx, error):
        """Handle errors in the translate command."""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Formato do comando incorreto. Use: `!translate <código_do_idioma> <texto>`")
        else:
            await ctx.send("❌ Ocorreu um erro ao processar sua solicitação.")

def setup(bot):
    bot.add_cog(Translate(bot))
