import nextcord
from nextcord.ext import commands

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="invite")
    async def generate_invite(self, ctx):
        """Generate an invite link for the bot."""
        invite_url = nextcord.utils.oauth_url(self.bot.user.id, permissions=nextcord.Permissions(permissions=8))

        embed = nextcord.Embed(
            title="Convite para me adicionar em outros servidores",
            description=f"Clique [aqui]({invite_url}) para me adicionar a um novo servidor!",
            color=nextcord.Color.green()
        )
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        embed.set_footer(text="Obrigado por me adicionar ao teu servidor!")

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Invite(bot))
