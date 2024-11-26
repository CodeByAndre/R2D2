import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

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
        """Creates a reaction role message."""
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ Não tens permissão para usar este comando.", ephemeral=True
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
            await interaction.response.send_message(
                f"❌ Ocorreu um erro ao configurar a reação: {e}", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        """Handles adding roles when a reaction is added."""
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
                            await channel.send(
                                f"{member.mention} foi adicionado ao cargo {role.name}.",
                                delete_after=5,
                            )
                        except Exception as e:
                            print(f"Erro ao adicionar o cargo: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        """Handles removing roles when a reaction is removed."""
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
                        await channel.send(
                            f"{member.mention} foi removido do cargo {role.name}.",
                            delete_after=5,
                        )
                    except Exception as e:
                        print(f"Erro ao remover o cargo: {e}")

def setup(bot):
    bot.add_cog(ReactionRole(bot))
