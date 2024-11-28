import nextcord
from nextcord.ext import commands

class KyerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_user_id = 268150813602349056  # User to monitor
        self.owner_id = 516735882259333132        # Your Discord ID
        self.active = False                      # Whether the control is active

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.active or member.id != self.target_user_id:
            return

        if not after.self_mute or not after.self_deaf:
            try:
                await member.edit(mute=True, deafen=True)
                print(f"Muted and deafened {member.display_name} in {member.guild.name}.")
            except nextcord.Forbidden:
                print("The bot lacks permission to mute or deafen the user.")
            except nextcord.HTTPException as e:
                print(f"Failed to mute or deafen {member.display_name}: {e}")

    @commands.command(name="ativarkyer")
    async def ativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("You do not have permission to use this command.")
            return

        self.active = True
        await ctx.send("Kyer control activated! The target user will be muted and deafened if they unmute or undeafen.")

    @commands.command(name="desativarkyer")
    async def desativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("You do not have permission to use this command.")
            return

        self.active = False
        await ctx.send("Kyer control deactivated!")

def setup(bot):
    bot.add_cog(KyerControl(bot))
