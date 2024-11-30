import nextcord
from nextcord.ext import commands

class DisconnectControl(commands.Cog):
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

        await self.enforce_disconnect(member)

    async def enforce_disconnect(self, member):
        if member.id in self.enforced_users:
            return

        self.enforced_users.add(member.id)
        try:
            if member.voice and member.voice.channel:
                await member.move_to(channel=None)  # Disconnect the user
                print(f"Disconnected {member.display_name} from voice channel in {member.guild.name}.")
        except nextcord.Forbidden:
            print("The bot does not have permission to disconnect the user.")
        except nextcord.HTTPException as e:
            print(f"Failed to disconnect {member.display_name}: {e}")
        finally:
            self.enforced_users.discard(member.id)

    @commands.command(name="activedisconnect")
    async def activedisconnect(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("❌ Nao tens permissoes para usar este comando.")
            return

        self.active = True

        guild = ctx.guild
        member = guild.get_member(self.target_user_id)
        if member and member.voice:
            await self.enforce_disconnect(member)

        await ctx.send("✅ Disconnect control ativo!")

    @commands.command(name="deactivedisconnect")
    async def deactivedisconnect(self, ctx):
        if ctx.author.id != self.owner_id:
            await ctx.send("❌ Nao tens permissoes para usar este comando.")
            return

        self.active = False
        self.enforced_users.clear()
        await ctx.send("✅ Disconnect control desativo!")

    @commands.command(name="setdisconnect")
    async def setdisconnect(self, ctx, user_id: int):
        if ctx.author.id != self.owner_id:
            await ctx.send("❌ Nao tens permissoes para usar este comando.")
            return
        try:
            user = await self.bot.fetch_user(user_id)
            self.target_user_id = user_id
            await ctx.send(f"✅ Utilizador setado para {user.mention}.")
        except nextcord.NotFound:
            await ctx.send("❌ Não foi possível encontrar o utilizador com o ID fornecido.")
        except nextcord.HTTPException as e:
            await ctx.send(f"❌ Ocorreu um erro ao buscar o utilizador: {e}")

def setup(bot):
    bot.add_cog(DisconnectControl(bot))
