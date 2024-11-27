import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, ButtonStyle
from nextcord.ui import View, Button

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @nextcord.slash_command(name="help", description="Displays the help menu.")
    async def help_command(self, interaction: Interaction):
        """Displays the help menu with a button for admin commands."""
        embed = nextcord.Embed(
            title="Help Menu",
            description="Explore the available commands below:",
            color=nextcord.Color.blurple(),
        )

        embed.add_field(
            name=":musical_note: | Music",
            value="`play`, `queue`, `skip`, `pause`, `resume`, `stop`",
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
            value="`ping` - Check bot latency",
            inline=False
        )

        prefix = "/"
        embed.set_footer(text=f"Prefix: {prefix}")

        admin_button = Button(label="Admin Commands", style=ButtonStyle.red)

        async def admin_button_callback(interaction: Interaction):
            if interaction.user.id == 516735882259333132 or interaction.user.guild_permissions.administrator:
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
                        "`prefix` - Change the bot's prefix\n"
                        "`welcome` - Set a welcome message"
                    ),
                    inline=False
                )
                admin_embed.set_footer(
                    text="Os comandos de admin estão restritos apenas para adminitradores."
                )
                await interaction.response.send_message(embed=admin_embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "⚠️ Não tens permissões para ver estes comandos.", ephemeral=True
                )

        admin_button.callback = admin_button_callback

        view = View()
        view.add_item(admin_button)

        await interaction.response.send_message(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Help(bot))
