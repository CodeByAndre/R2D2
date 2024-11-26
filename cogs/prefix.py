from nextcord.ext import commands
from pymongo import MongoClient
import os

class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["prefixes"]

    @commands.command(name="prefix")
    @commands.has_permissions(administrator=True)
    async def change_prefix(self, ctx, new_prefix: str):
        if len(new_prefix) > 5:
            await ctx.send("O prefixo é muito longo! Tente algo com até 5 caracteres.", delete_after=3)
            return

        self.collection.update_one(
            {"server_id": ctx.guild.id},
            {"$set": {"prefix": new_prefix}},
            upsert=True
        )
        await ctx.send(f"O prefixo foi alterado para `{new_prefix}`!", delete_after=3)
    
    @change_prefix.error
    async def change_prefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Apenas administradores podem alterar o prefixo.", delete_after=3)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Por favor, forneça um novo prefixo. Exemplo: `/prefix .`", delete_after=3)
        else:
            await ctx.send("Ocorreu um erro ao tentar alterar o prefixo.", delete_after=3)

def setup(bot):
    bot.add_cog(Prefix(bot))
