import os
from nextcord.ext import commands
from nextcord import Embed
from pymongo import MongoClient
from openai import AsyncOpenAI


class Gerar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["keys"]

        api_key_doc = self.collection.find_one({"name": "OPENAI_API_KEY"})
        if not api_key_doc:
            raise ValueError("Chave da API OpenAI não encontrada no banco de dados!")
        self.openai_key = api_key_doc["value"]
        self.client_openai = AsyncOpenAI(api_key=self.openai_key)

    @commands.command(name="txt")
    async def generate_text(self, ctx, *, prompt: str):
        """Generate text using OpenAI's GPT model."""
        try:
            response = await self.client_openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content.strip()
            await ctx.send(content)
        except Exception as e:
            await ctx.send(f"❌ Erro ao gerar conteúdo: {e}")

    @commands.command(name="img")
    async def generate_image(self, ctx, *, prompt: str):
        """Generate an image using OpenAI's DALL-E."""
        if ctx.author.id != 516735882259333132 and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Apenas os dono do bot podem usar este comando.")
            return
        try:
            warning_msg = await ctx.send("🔄 Gerando a imagem. Isso pode levar alguns segundos!")

            response = await self.client_openai.images.generate(
                prompt=prompt,
                size="1024x1024"
            )
            image_url = response.data[0].url

            embed = Embed(
                title="Aqui está sua imagem!",
                description=f"Prompt: {prompt}",
                color=0x00ff00
            )
            embed.set_image(url=image_url)
            embed.set_footer(text="Imagem gerada por: R2D2")

            await warning_msg.delete()
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Erro ao gerar a imagem: {e}")

def setup(bot):
    bot.add_cog(Gerar(bot))
