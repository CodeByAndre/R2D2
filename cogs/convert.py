import nextcord
from nextcord.ext import commands
import aiohttp
from pymongo import MongoClient
import os

class CurrencyConverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["keys"]

        # Fetch API key from the database
        api_key_entry = self.collection.find_one({"name": "EXCHANGE_RATE_API_KEY"})
        if not api_key_entry or "value" not in api_key_entry:
            raise ValueError("API key for Exchange Rate API not found in the database.")
        self.api_key = api_key_entry["value"]
        self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest"

    @commands.command(name="convert")
    async def convert(self, ctx, amount: float, from_currency: str, to_currency: str):
        """Converts currency from one type to another."""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if amount <= 0:
            await ctx.send("O valor deve ser maior que 0.")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/{from_currency}") as response:
                    data = await response.json()

            if response.status == 200 and "conversion_rates" in data:
                rates = data["conversion_rates"]
                if to_currency in rates:
                    conversion_rate = rates[to_currency]
                    converted_amount = amount * conversion_rate
                    embed = nextcord.Embed(
                        title="💱 Conversão de Moedas",
                        description=f"{amount} {from_currency} equivale a {converted_amount:.2f} {to_currency}.",
                        color=nextcord.Color.green()
                    )
                    embed.add_field(name="Taxa de Conversão", value=f"1 {from_currency} = {conversion_rate:.4f} {to_currency}")
                    embed.set_footer(text="Dados obtidos por: R2D2")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"A moeda de destino `{to_currency}` não foi encontrada.")
            else:
                await ctx.send("Houve um problema ao obter as taxas de câmbio. Verifique os códigos das moedas.")
        except Exception as e:
            await ctx.send(f"Ocorreu um erro ao tentar converter: {e}")

def setup(bot):
    bot.add_cog(CurrencyConverter(bot))
