import nextcord
from nextcord.ext import commands

class KyerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_user_id = 1303516704491704351
        self.owner_id = 516735882259333132
        self.active = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.active or member.id != self.target_user_id:
            return

        if not after.self_mute or not after.self_deaf:
            guild = member.guild
            bot_member = guild.me

            if bot_member.voice:
                await bot_member.edit(mute=True, deafen=True)

    @commands.command(name="ativarkyer")
    async def ativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("You do not have permission to use this command.")
            return

        self.active = True
        await ctx.send("Kyer control activated! The bot will automatically mute and deafen.")

    @commands.command(name="desativarkyer")
    async def desativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("You do not have permission to use this command.")
            return

        self.active = False
        await ctx.send("Kyer control deactivated!")

def setup(bot):
    bot.add_cog(KyerControl(bot))
