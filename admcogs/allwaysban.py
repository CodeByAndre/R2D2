import nextcord
from nextcord.ext import commands
from pymongo import MongoClient
import os

class AlwaysBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["always_banned_users"]
    
    def is_always_banned(self, user_id):
        return self.collection.find_one({"user_id": user_id}) is not None
    
    @commands.command()
    async def alwaysban(self, ctx, user_id: int):
        "Bane permanentemente um usuário e impede que ele entre no servidor."
        user = await self.bot.fetch_user(user_id)
        if self.is_always_banned(user_id):
            await ctx.send(f"{user.name} já está na lista de banidos permanentemente.")
            return
        
        self.collection.insert_one({"user_id": user_id})
        await ctx.guild.ban(user, reason="Banimento permanente pelo alwaysban")
        await ctx.send(f"{user.name} foi banido permanentemente e não poderá voltar ao servidor.")
    
    @commands.command()
    async def removealwaysban(self, ctx, user_id: int):
        "Remove um usuário da lista de banidos permanentemente."
        if not self.is_always_banned(user_id):
            await ctx.send("Esse usuário não está na lista de banidos permanentemente.")
            return
        
        self.collection.delete_one({"user_id": user_id})
        await ctx.send("O usuário foi removido da lista de banidos permanentemente.")
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        "Impede que um usuário na lista de banidos reentre no servidor."
        if self.is_always_banned(member.id):
            await member.guild.ban(member, reason="Usuário banido permanentemente tentando entrar novamente.")
            
def setup(bot):
    bot.add_cog(AlwaysBan(bot))