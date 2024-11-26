import nextcord
from nextcord.ext import commands

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar")
    async def avatar(self, ctx, member: nextcord.Member = None):
        """Fetches and displays the avatar of a user."""
        member = member or ctx.author

        embed = nextcord.Embed(
            title=f"Avatar de {member}",
            description=f"[Clica para baixar]({member.display_avatar.url})",
            colour=nextcord.Color.random()
        )
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Avatar(bot))
