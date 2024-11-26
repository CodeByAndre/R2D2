import os
import sys
import subprocess
from nextcord.ext import commands
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class Reboot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["reboot_status"]

    @commands.command(name="reboot")
    @commands.is_owner()
    async def reboot_bot(self, ctx):
        """Command to reboot the bot."""
        confirmation_msg = await ctx.send("Rebooting...")

        self.collection.update_one(
            {"_id": "reboot_status"},
            {"$set": {"channel_id": ctx.channel.id, "message_id": confirmation_msg.id}},
            upsert=True
        )

        await ctx.message.delete()

        python_executable = sys.executable
        script_path = os.path.abspath("main.py")

        subprocess.Popen([python_executable, script_path])

        await self.bot.close()
        os._exit(0)

    @reboot_bot.error
    async def reboot_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("You do not have permission to use this command.", delete_after=5)

def setup(bot):
    bot.add_cog(Reboot(bot))
