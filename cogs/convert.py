import nextcord
from nextcord.ext import commands
import aiohttp
from pymongo import MongoClient
import os
import logging

logger = logging.getLogger("DiscordBot")

class CurrencyConverter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["keys"]

        api_key_entry = self.collection.find_one({"name": "EXCHANGE_RATE_API_KEY"})
        if not api_key_entry or "value" not in api_key_entry:
            raise ValueError("API key for Exchange Rate API not found in the database.")
        self.api_key = api_key_entry["value"]
        self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest"

    @nextcord.slash_command(name="convert", description="Converts currency from one type to another.")
    async def convert(self, interaction: nextcord.Interaction, amount: float, from_currency: str, to_currency: str):
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if amount <= 0:
            await interaction.response.send_message("O valor deve ser maior que 0.", ephemeral=True)
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
                    logger.info(f"Slash command 'convert' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {amount} {from_currency} para {to_currency}")
                    await interaction.response.send_message(embed=embed)
                else:
                    logger.error(f"Moeda de destino `{to_currency}` não encontrada no comando 'convert' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}")
                    await interaction.response.send_message(f"A moeda de destino `{to_currency}` não foi encontrada.", ephemeral=True)
            else:
                logger.error(f"Erro ao obter taxas de câmbio no comando 'convert' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}")
                await interaction.response.send_message("Houve um problema ao obter as taxas de câmbio. Verifique os códigos das moedas.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro no comando 'convert' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {e}")
            await interaction.response.send_message(f"Ocorreu um erro ao tentar converter: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(CurrencyConverter(bot))
