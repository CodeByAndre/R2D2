import nextcord
from nextcord.ext import commands

class KyerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_user_id = 268150813602349056
        self.owner_id = 516735882259333132
        self.active = False
        self.enforced_users = set()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not self.active or member.id != self.target_user_id:
            return

        await self.enforce_mute_deafen(member)

    async def enforce_mute_deafen(self, member):
        if member.id in self.enforced_users:
            return

        self.enforced_users.add(member.id)
        try:
            if not member.voice.mute or not member.voice.deaf:
                await member.edit(mute=True, deafen=True)
                print(f"Muted and deafened {member.display_name} in {member.guild.name}.")
        except nextcord.Forbidden:
            print("The bot does not have permission to mute and deafen.")
        except nextcord.HTTPException as e:
            print(f"Failed to mute or deafen {member.display_name}: {e}")
        finally:
            self.enforced_users.discard(member.id)

    @commands.command(name="ativarkyer")
    async def ativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("❌ Nao tens permissoes para usar este comando.")
            return

        self.active = True

        guild = ctx.guild
        member = guild.get_member(self.target_user_id)
        if member and member.voice:
            await self.enforce_mute_deafen(member)

        await ctx.send("✅ Kyer control ativo!")

    @commands.command(name="desativarkyer")
    async def desativarkyer(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("❌ Nao tens permissoes para usar este comando.")
            return

        self.active = False
        self.enforced_users.clear()
        await ctx.send("✅ Kyer control desativo!")

    @commands.command(name="setkyer")
    async def setkyer(self, ctx, user_id: int):
        if ctx.author.id != self.owner_id:
            await ctx.send("❌ Nao tens permissoes para usar este comando.")
            return

        guild = ctx.guild
        member = guild.get_member(user_id)
        if member:
            self.target_user_id = user_id
            await ctx.send(f"✅ Utilizador setado para {member.mention}.")

            if self.active and member.voice:
                await self.enforce_mute_deafen(member)
        else:
            await ctx.send("❌ Não foi possível encontrar o utilizador com o ID fornecido.")

def setup(bot):
    bot.add_cog(KyerControl(bot))
