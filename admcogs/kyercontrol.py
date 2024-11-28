import nextcord
from nextcord.ext import commands

class KyerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_user_id = 268150813602349056
        self.owner_id = 516735882259333132
        self.active = False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.active or member.id != self.target_user_id:
            return

        if not after.self_mute or not after.self_deaf:
            try:
                await member.edit(mute=True, deafen=True)
                print(f"Muted e deafened {member.display_name} em {member.guild.name}.")
            except nextcord.Forbidden:
                print("O bot nao tem permissoes para dar mute e deafen.")
            except nextcord.HTTPException as e:
                print(f"Failed to mute or deafen {member.display_name}: {e}")

    @commands.command(name="ativarkyer")
    async def ativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("Nao tens permissoes para usar este comando.")
            return

        self.active = True
        await ctx.send("Kyer control ativado!")

    @commands.command(name="desativarkyer")
    async def desativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("Nao tens permissoes para usar este comando.")
            return

        self.active = False
        await ctx.send("Kyer control desativado!")

def setup(bot):
    bot.add_cog(KyerControl(bot))
