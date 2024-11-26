import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ButtonStyle
from nextcord.ui import Button, View
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["prefixes"]
        self.bot.remove_command("help")

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Displays the help menu with a button for admin commands."""
        prefix_entry = self.collection.find_one({"server_id": ctx.guild.id})
        prefix = prefix_entry["prefix"] if prefix_entry else "/"

        embed = nextcord.Embed(
            title="Help Menu",
            description="Explore the available commands below:",
            color=nextcord.Color.blurple(),
        )

        embed.add_field(
            name=":musical_note: | Music",
            value="`play`, `add`, `skip`, `pause`, `resume`, `stop`, `queue`",
            inline=False
        )

        embed.add_field(
            name=":game_die: | Games",
            value=(
                "`galo` - Start the game\n"
                "`futebolada` - Create teams\n"
                "  ↳ `player` - Add a player\n"
                "  ↳ `rplayer` - Remove a player\n"
                "  ↳ `players` - List all players"
            ),
            inline=False
        )

        embed.add_field(
            name=":speech_balloon: | General",
            value=(
                "`ping` - Check bot latency"
                "`txt` - generate text\n"
                "`img` - generate images\n"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Prefix: {prefix}",
            icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
        )

        admin_button = Button(label="Admin Commands", style=ButtonStyle.red)

        async def admin_button_callback(interaction: Interaction):
            """Callback to display admin commands."""
            if interaction.user.guild_permissions.administrator:
                admin_embed = nextcord.Embed(
                    title="Admin Commands",
                    description="Here are the admin-specific commands:",
                    color=nextcord.Color.red(),
                )
                admin_embed.add_field(
                    name=":tools: | Admin Commands",
                    value=(
                        "`ban` - Ban a user\n"
                        "`clean` - Delete messages\n"
                        "`kick` - Kick a user\n"
                        "`mutechannel` - Mute the current channel\n"
                        "`reaction` - Add a reaction role\n"
                        "`reboot` - Reboot the bot\n"
                        "`unban` - Unban a user\n"
                        "`prefix` - Change the bot prefix\n"
                        "`welcome` - Set a welcome message"
                    ),
                    inline=False
                )
                admin_embed.set_footer(
                    text=f"Prefix: {prefix}",
                )
                await interaction.response.send_message(embed=admin_embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "You don't have permission to view admin commands.", ephemeral=True
                )

        admin_button.callback = admin_button_callback

        view = View()
        view.add_item(admin_button)

        await ctx.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Help(bot))
