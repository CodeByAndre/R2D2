import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ButtonStyle
from nextcord.ui import View, Button
import logging

logger = logging.getLogger("DiscordBot")


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if "help" in self.bot.commands:
            self.bot.remove_command("help")

    @nextcord.slash_command(name="help", description="Exibe o menu de ajuda.")
    async def help_command(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        async def show_initial_menu():
            """Display the initial help menu."""
            embed = nextcord.Embed(
                title="Menu de Ajuda",
                description="Explore os comandos disponíveis abaixo:",
                color=nextcord.Color.blurple(),
            )
            embed.add_field(
                name=":musical_note: | Música",
                value="`play`, `queue`, `skip`, `pause`, `resume`, `stop`",
                inline=False,
            )
            embed.add_field(
                name=":game_die: | Jogos",
                value=(
                    "`galo` - Inicia o jogo\n"
                    "`futebolada` - Cria equipas\n"
                    "  ↳ `player` - Adiciona um jogador\n"
                    "  ↳ `rplayer` - Remove um jogador\n"
                    "  ↳ `players` - Lista todos os jogadores"
                ),
                inline=False,
            )
            embed.add_field(
                name=":speech_balloon: | Geral",
                value=(
                    "`ping` - Verifica a latência do bot\n"
                    "`invite` - Convida o bot\n"
                    "`translate` - Traduza palavras/frases\n"
                    "`txt` - Ajuda de texto com IA\n"
                    "`img` - Criador de imagens com IA\n"
                    "`acordar` - Move um utilizador entre canais de voz\n"
                ),
                inline=False,
            )
            embed.set_footer(text="Prefixo: /")

            view = View(timeout=180)

            botao_admin = Button(label="Comandos de Admin", style=ButtonStyle.red)
            botao_owner = Button(label="Comandos do Dono", style=ButtonStyle.green)

            async def botao_admin_callback(interaction: Interaction):
                if interaction.user.guild_permissions.administrator:
                    await send_admin_commands_dm(interaction)
                else:
                    await interaction.response.send_message(
                        "⚠️ Não tens permissões para ver estes comandos.", ephemeral=True
                    )

            async def botao_owner_callback(interaction: Interaction):
                if interaction.user.id == 516735882259333132:
                    await send_owner_commands_dm(interaction)
                else:
                    await interaction.response.send_message(
                        "⚠️ Apenas o dono do bot pode ver estes comandos.", ephemeral=True
                    )

            botao_admin.callback = botao_admin_callback
            botao_owner.callback = botao_owner_callback

            view.add_item(botao_admin)
            if interaction.user.id == 516735882259333132:
                view.add_item(botao_owner)

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        async def send_admin_commands_dm(interaction: Interaction):
            """Send admin commands directly to the user's DM."""
            admin_embed = nextcord.Embed(
                title="Comandos de Admin",
                description="Aqui estão os comandos exclusivos para administradores:",
                color=nextcord.Color.red(),
            )
            admin_embed.add_field(
                name=":tools: | Comandos de Admin",
                value=(
                    "`ban` - Banir um utilizador\n"
                    "`unban` - Revogar banimento de um utilizador\n"
                    "`clean` - Apagar mensagens\n"
                    "`kick` - Expulsar um utilizador\n"
                    "`mutechannel` - Silenciar o canal atual\n"
                    "`reaction` - Adicionar um papel de reação\n"
                    "`reboot` - Reiniciar o bot\n"
                    "`prefix` - Alterar o prefixo do bot\n"
                    "`setwelcome` - Configurar uma mensagem de boas-vindas"
                ),
                inline=False,
            )
            admin_embed.set_footer(text="Os comandos de admin estão restritos apenas para administradores.")

            try:
                await interaction.user.send(embed=admin_embed)
                await interaction.response.send_message("✅ Os comandos de admin foram enviados para sua DM!", ephemeral=True)
            except nextcord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ Não consegui enviar uma mensagem para sua DM. Verifique se está habilitado.", ephemeral=True
                )

        async def send_owner_commands_dm(interaction: Interaction):
            """Send owner commands directly to the user's DM."""
            owner_embed = nextcord.Embed(
                title="Comandos do Dono",
                description="Aqui estão os comandos exclusivos para o dono do bot:",
                color=nextcord.Color.green(),
            )
            owner_embed.add_field(
                name=":crown: | Comandos do Dono",
                value=(
                    "`ativardisconnect` - Impede alguém de conectar a canais de voz\n"
                    "`desativardisconnect` - Remove a restrição de conexão\n"
                    "`setdisconnect` - Configura a pessoa\n"
                    "`ativarkyer` - Impede alguém de desmutar/undeafen\n"
                    "`desativarkyer` - Remove a restrição de desmutar/undeafen\n"
                    "`setkyer` - Configura a pessao\n"
                    "`tm` - Executa comandos no terminal do servidor\n"
                    "`reboot` - Reinicia o bot"
                ),
                inline=False,
            )
            owner_embed.set_footer(text="Os comandos do dono são restritos ao proprietário do bot.")

            try:
                await interaction.user.send(embed=owner_embed)
                await interaction.response.send_message("✅ Os comandos do dono foram enviados para sua DM!", ephemeral=True)
            except nextcord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ Não consegui enviar uma mensagem para sua DM. Verifique se está habilitado.", ephemeral=True
                )
        await show_initial_menu()


def setup(bot):
    bot.add_cog(Help(bot))
