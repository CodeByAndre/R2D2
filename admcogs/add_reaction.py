import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import logging

logger = logging.getLogger("DiscordBot")

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = {}

    @nextcord.slash_command(name="react", description="Creates a reaction role message.")
    async def react(
        self,
        interaction: Interaction,
        message_text: str = SlashOption(description="Text to display in the message"),
        emoji: str = SlashOption(description="Emoji to react with"),
        role: nextcord.Role = SlashOption(description="Role to assign"),
    ):
        logger.info(
            f"Slash command 'react' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}"
        )

        if interaction.user.id != 516735882259333132 and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Apenas os administradores podem usar este comando.",
                ephemeral=True
            )
            return

        embed = nextcord.Embed(
            title="ADICIONAR CARGO",
            description=f"{message_text} ({role.mention})",
            color=nextcord.Color.blue(),
        )
        embed.set_footer(text="Reage para teres acesso ao servidor!")

        try:
            message = await interaction.channel.send(embed=embed)
            await message.add_reaction(emoji)
            self.reaction_roles[message.id] = (str(emoji), role)
            await interaction.response.send_message(
                "✅ Mensagem de reação criada com sucesso!", ephemeral=True
            )
        except Exception as e:
            logger.error(
                f"Erro no comando 'react' usado por {interaction.user} no server {interaction.guild.name}#{interaction.channel.name}: {e}"
            )
            await interaction.response.send_message(
                f"❌ Ocorreu um erro ao configurar a reação: {e}", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        if payload.member.bot:
            return

        if payload.message_id in self.reaction_roles:
            emoji, role = self.reaction_roles[payload.message_id]
            if str(payload.emoji) == emoji:
                guild = self.bot.get_guild(payload.guild_id)
                if guild:
                    member = guild.get_member(payload.user_id)
                    if member:
                        try:
                            await member.add_roles(role)
                            channel = self.bot.get_channel(payload.channel_id)
                            logger.info(
                                f"{member} recebeu o cargo '{role.name}' no server {guild.name}#{channel.name} após reagir com {emoji}"
                            )
                            await channel.send(
                                f"{member.mention} foi adicionado ao cargo {role.name}.",
                                delete_after=5,
                            )
                        except Exception as e:
                            logger.error(f"Erro ao adicionar o cargo '{role.name}' para {member}: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        if payload.message_id in self.reaction_roles:
            emoji, role = self.reaction_roles[payload.message_id]
            if str(payload.emoji) == emoji:
                member = guild.get_member(payload.user_id)
                if member:
                    try:
                        await member.remove_roles(role)
                        channel = self.bot.get_channel(payload.channel_id)
                        logger.info(
                            f"{member} perdeu o cargo '{role.name}' no server {guild.name}#{channel.name} após remover a reação {emoji}"
                        )
                        await channel.send(
                            f"{member.mention} foi removido do cargo {role.name}.",
                            delete_after=5,
                        )
                    except Exception as e:
                        logger.error(f"Erro ao remover o cargo '{role.name}' para {member}: {e}")

def setup(bot):
    bot.add_cog(ReactionRole(bot))
