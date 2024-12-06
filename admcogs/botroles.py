import nextcord
from nextcord.ext import commands

class BotRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="botroles")
    async def botroles(self, ctx):
        if ctx.author.id != 516735882259333132:
            await ctx.send("❌ Apenas o dono do bot pode usar este comando.", delete_after=10)
            return

        embed = nextcord.Embed(
            title="Papéis do Bot nos Servidores",
            description="Aqui estão os papéis que o bot possui em cada servidor e se têm permissões administrativas:",
            color=nextcord.Color.blurple(),
        )

        for guild in self.bot.guilds:
            bot_member = guild.me
            roles = bot_member.roles[1:]

            if not roles:
                role_info = "Sem papéis atribuídos"
            else:
                role_info = []
                for role in roles:
                    is_admin = "✅ Admin" if role.permissions.administrator else "❌ Não Admin"
                    role_info.append(f"{role.name} ({is_admin})")

                role_info = "\n".join(role_info)

            embed.add_field(name=guild.name, value=role_info, inline=False)

        try:
            await ctx.author.send(embed=embed)
            await ctx.send("✅ A lista de papéis foi enviada para sua DM.", delete_after=10)
        except nextcord.Forbidden:
            await ctx.send(
                "⚠️ Não consegui enviar uma mensagem para sua DM. Verifique se você habilitou mensagens privadas.", delete_after=10
            )

def setup(bot):
    bot.add_cog(BotRoles(bot))
