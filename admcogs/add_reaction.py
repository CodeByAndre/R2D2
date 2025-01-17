import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import logging
from pymongo import MongoClient
import os

logger = logging.getLogger("DiscordBot")

class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = {}

        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["reaction_roles"]

        self.load_reaction_roles()

    def load_reaction_roles(self):
        for document in self.collection.find():
            message_id = document["message_id"]
            self.reaction_roles[message_id] = (document["emoji"], document["role_id"])
        logger.info("Reação-cargos carregados da base de dados.")

    def save_reaction_role(self, message_id, emoji, role_id):
        self.collection.update_one(
            {"message_id": message_id},
            {"$set": {"emoji": emoji, "role_id": role_id}},
            upsert=True
        )

    def remove_reaction_role(self, message_id):
        self.collection.delete_one({"message_id": message_id})

    @nextcord.slash_command(name="react", description="Da uma role com reações.")
    async def react(
        self,
        interaction: Interaction,
        message_text: str = SlashOption(description="Texto da mensagem"),
        emoji: str = SlashOption(description="Emoji para reagir"),
        role: nextcord.Role = SlashOption(description="Role a dar"),
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

            self.reaction_roles[message.id] = (str(emoji), role.id)
            self.save_reaction_role(message.id, str(emoji), role.id)

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
            emoji, role_id = self.reaction_roles[payload.message_id]
            if str(payload.emoji) == emoji:
                guild = self.bot.get_guild(payload.guild_id)
                if guild:
                    member = guild.get_member(payload.user_id)
                    role = guild.get_role(role_id)
                    if member and role:
                        try:
                            await member.add_roles(role)
                            channel = self.bot.get_channel(payload.channel_id)
                            logger.info(
                                f"{member} recebeu o cargo '{role.name}' no server {guild.name}#{channel.name} após reagir com {emoji}"
                            )
                        except Exception as e:
                            logger.error(f"Erro ao adicionar o cargo '{role.name}' para {member}: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        if payload.message_id in self.reaction_roles:
            emoji, role_id = self.reaction_roles[payload.message_id]
            if str(payload.emoji) == emoji:
                member = guild.get_member(payload.user_id)
                role = guild.get_role(role_id)
                if member and role:
                    try:
                        await member.remove_roles(role)
                        channel = self.bot.get_channel(payload.channel_id)
                        logger.info(
                            f"{member} perdeu o cargo '{role.name}' no server {guild.name}#{channel.name} após remover a reação {emoji}"
                        )
                    except Exception as e:
                        logger.error(f"Erro ao remover o cargo '{role.name}' para {member}: {e}")

def setup(bot):
    bot.add_cog(ReactionRole(bot))
