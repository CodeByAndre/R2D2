import nextcord
from nextcord.ext import commands
from nextcord import ui, Interaction, SlashOption
from pymongo import MongoClient
from datetime import datetime
import logging
import os

logger = logging.getLogger("DiscordBot")

# ------------------------ MODAL PARA ABRIR TICKET ------------------------
class TicketModal(ui.Modal):
    def __init__(self, bot, perguntas, tickets_collection):
        super().__init__("Abrir Ticket")
        self.bot = bot
        self.tickets_collection = tickets_collection
        self.perguntas = perguntas
        self.inputs = []
        for pergunta in perguntas:
            input_box = ui.TextInput(
                label=pergunta,
                placeholder=f"Resposta para: {pergunta}",
                required=True,
                style=nextcord.TextInputStyle.paragraph if len(pergunta) > 30 else nextcord.TextInputStyle.short,
                max_length=200
            )
            self.add_item(input_box)
            self.inputs.append(input_box)

    async def callback(self, interaction: Interaction):
        guild = interaction.guild
        categoria = nextcord.utils.get(guild.categories, name="Tickets")
        if categoria is None:
            overwrites = {guild.default_role: nextcord.PermissionOverwrite(view_channel=False)}
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = nextcord.PermissionOverwrite(view_channel=True)
            categoria = await guild.create_category("Tickets", overwrites=overwrites)

        ultimo_ticket = self.tickets_collection.find_one(
            {"guild_id": str(guild.id)}, sort=[("ticket_num", -1)]
        )
        ticket_num = 1 if ultimo_ticket is None else ultimo_ticket["ticket_num"] + 1

        respostas_dict = {inp.label: inp.value for inp in self.inputs}

        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            interaction.user: nextcord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites,
            topic=f"Ticket #{ticket_num}"
        )

        respostas_texto = "\n".join([f"**{pergunta}:** {resposta}" for pergunta, resposta in respostas_dict.items()])
        await channel.send(
            f"👋 {interaction.user.mention}, obrigado por abrir um ticket!\n{respostas_texto}"
        )

        self.tickets_collection.update_one(
            {"channel_id": channel.id},
            {"$set": {
                "guild_id": str(guild.id),
                "user_id": interaction.user.id,
                "channel_id": channel.id,
                "ticket_num": ticket_num,
                "respostas": respostas_dict,
                "status": "aberto",
                "claimed_by": None,
                "data_criacao": datetime.utcnow()
            }},
            upsert=True
        )

        embed = nextcord.Embed(
            title="Gestão de Ticket",
            description=f"**Ticket Nº:** {ticket_num}",
            color=nextcord.Color.green()
        )
        for pergunta, resposta in respostas_dict.items():
            embed.add_field(name=pergunta, value=resposta or "Não respondido", inline=False)

        msg = await channel.send(
            embed=embed,
            view=TicketControlView(self.bot, self.tickets_collection, interaction.user.id)
        )

        self.tickets_collection.update_one(
            {"channel_id": channel.id},
            {"$set": {"control_message_id": msg.id}},
            upsert=True
        )

        await interaction.response.send_message(f"✅ Ticket criado: {channel.mention}", ephemeral=True)

# ------------------------ BOTÕES ------------------------
class ClaimButton(ui.Button):
    def __init__(self, bot, tickets_collection):
        super().__init__(label="Assumir", style=nextcord.ButtonStyle.blurple)
        self.bot = bot
        self.tickets_collection = tickets_collection

    async def callback(self, interaction: Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem assumir tickets.", ephemeral=True)
            return

        ticket = self.tickets_collection.find_one({"channel_id": interaction.channel.id})
        if ticket is None or ticket.get("claimed_by"):
            await interaction.response.send_message("❌ Este ticket já foi assumido ou não existe.", ephemeral=True)
            return

        self.tickets_collection.update_one(
            {"channel_id": interaction.channel.id}, {"$set": {"claimed_by": interaction.user.id}}
        )

        control_msg_id = ticket.get("control_message_id")
        if control_msg_id:
            try:
                msg = await interaction.channel.fetch_message(control_msg_id)
                embed = msg.embeds[0]
                embed.set_footer(text=f"Assumido por: {interaction.user.display_name}")
                await msg.edit(embed=embed)
            except:
                pass

        user = interaction.guild.get_member(ticket["user_id"])
        if user:
            await user.send(f"📌 O seu ticket #{ticket['ticket_num']} foi assumido por {interaction.user.mention}.")
        await interaction.response.send_message("✅ Ticket assumido.", ephemeral=True)

class CloseButton(ui.Button):
    def __init__(self, bot, tickets_collection):
        super().__init__(label="Encerrar", style=nextcord.ButtonStyle.red)
        self.bot = bot
        self.tickets_collection = tickets_collection

    async def callback(self, interaction: Interaction):
        ticket = self.tickets_collection.find_one({"channel_id": interaction.channel.id})
        if ticket is None:
            await interaction.response.send_message("❌ Ticket não encontrado na DB.", ephemeral=True)
            return
        if ticket.get("claimed_by") != interaction.user.id:
            await interaction.response.send_message("❌ Apenas quem assumiu pode encerrar o ticket.", ephemeral=True)
            return

        self.tickets_collection.update_one({"channel_id": interaction.channel.id}, {"$set": {"status": "fechado"}})
        await interaction.channel.send(f"✅ Ticket encerrado por {interaction.user.mention}. O canal será removido em breve.")
        await interaction.channel.delete()

# ------------------------ VIEW DOS BOTÕES ------------------------
class TicketControlView(ui.View):
    def __init__(self, bot, tickets_collection, ticket_owner_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.tickets_collection = tickets_collection
        self.add_item(ClaimButton(bot, tickets_collection))
        self.add_item(CloseButton(bot, tickets_collection))

class TicketView(ui.View):
    def __init__(self, bot, questions_collection, tickets_collection):
        super().__init__(timeout=None)
        self.bot = bot
        self.questions_collection = questions_collection
        self.tickets_collection = tickets_collection

    @ui.button(label="Abrir Ticket", style=nextcord.ButtonStyle.green)
    async def abrir_ticket(self, button: ui.Button, interaction: Interaction):
        perguntas_doc = self.questions_collection.find_one({"guild_id": str(interaction.guild.id)})
        perguntas = perguntas_doc["perguntas"] if perguntas_doc and "perguntas" in perguntas_doc else ["Motivo", "Descrição"]
        await interaction.response.send_modal(TicketModal(self.bot, perguntas, self.tickets_collection))

# ------------------------ COG ------------------------
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]

        self.questions_collection = self.db["ticket_questions"]
        self.questions_collection.create_index("guild_id", unique=True)

        self.tickets_collection = self.db["tickets"]
        self.tickets_collection.create_index("channel_id", unique=True)
        self.tickets_collection.create_index([("guild_id", 1), ("ticket_num", 1)])
        self.tickets_collection.create_index([("guild_id", 1), ("user_id", 1)])
        self.tickets_collection.create_index("status")

    @nextcord.slash_command(name="ticketcreate", description="Cria mensagem com botão para abrir tickets")
    async def ticketcreate(self, interaction: Interaction, message_text: str = SlashOption(description="Texto da mensagem")):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas admins podem usar este comando.", ephemeral=True)
            return

        embed = nextcord.Embed(
            title="Sistema de Tickets",
            description=message_text,
            color=nextcord.Color.blue()
        )

        sent_msg = await interaction.channel.send(embed=embed, view=TicketView(self.bot, self.questions_collection, self.tickets_collection))

        self.questions_collection.update_one(
            {"guild_id": str(interaction.guild.id)},
            {"$set": {"message_id": sent_msg.id, "channel_id": interaction.channel.id}},
            upsert=True
        )
        await interaction.response.send_message("✅ Mensagem de ticket enviada!", ephemeral=True)

    @nextcord.slash_command(name="ticketquestions", description="Define perguntas do ticket")
    async def ticketquestions(self, interaction: Interaction, perguntas_texto: str = SlashOption(description="Perguntas separadas por ';'")):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
            return

        novas_perguntas = [p.strip() for p in perguntas_texto.split(";") if p.strip()]
        if not novas_perguntas:
            await interaction.response.send_message("❌ Tens de fornecer pelo menos uma pergunta.", ephemeral=True)
            return

        self.questions_collection.update_one(
            {"guild_id": str(interaction.guild.id)},
            {"$set": {"perguntas": novas_perguntas}},
            upsert=True
        )
        await interaction.response.send_message(f"✅ Perguntas atualizadas: {', '.join(novas_perguntas)}", ephemeral=True)

    @nextcord.slash_command(name="ticketsearch", description="Pesquisa tickets por filtros")
    async def ticketsearch(
        self,
        interaction: Interaction,
        aberto_por: nextcord.Member = SlashOption(required=False, description="Pessoa que abriu o ticket"),
        assumido_por: nextcord.Member = SlashOption(required=False, description="Pessoa que assumiu o ticket"),
        numero_ticket: int = SlashOption(required=False, description="Número do ticket"),
        status: str = SlashOption(required=False, choices=["aberto", "fechado"], description="Filtrar por status")
    ):
        query = {"guild_id": str(interaction.guild.id)}
        if aberto_por:
            query["user_id"] = aberto_por.id
        if assumido_por:
            query["claimed_by"] = assumido_por.id
        if numero_ticket:
            query["ticket_num"] = numero_ticket
        if status:
            query["status"] = status

        resultados = list(self.tickets_collection.find(query))
        if not resultados:
            await interaction.response.send_message("❌ Nenhum ticket encontrado com esses filtros.", ephemeral=True)
            return

        embed = nextcord.Embed(title="Resultados da pesquisa de tickets", color=nextcord.Color.orange())
        for ticket in resultados:
            dono = interaction.guild.get_member(ticket["user_id"])
            claim_user = interaction.guild.get_member(ticket["claimed_by"]) if ticket.get("claimed_by") else None

            respostas = "\n".join([f"**{pergunta}:** {resposta}" for pergunta, resposta in ticket.get("respostas", {}).items()])

            embed.add_field(
                name=f"Ticket #{ticket['ticket_num']} ({ticket['status']})",
                value=(
                    f"👤 Aberto por: {dono.mention if dono else 'Desconhecido'}\n"
                    f"📌 Assumido por: {claim_user.mention if claim_user else 'Ninguém'}\n"
                    f"📂 Canal: <#{ticket['channel_id']}>\n"
                    f"📝 **Perguntas e Respostas:**\n{respostas}"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def restore_ticket_buttons(self):
        for guild in self.bot.guilds:
            doc = self.questions_collection.find_one({"guild_id": str(guild.id)})
            if doc:
                channel_id = doc.get("channel_id")
                message_id = doc.get("message_id")
                if channel_id and message_id:
                    channel = guild.get_channel(channel_id)
                    if channel:
                        try:
                            msg = await channel.fetch_message(message_id)
                            await msg.edit(view=TicketView(self.bot, self.questions_collection, self.tickets_collection))
                            logger.info(f"✅ Restaurado botão Abrir Ticket em {guild.name}#{channel.name}")
                        except Exception as e:
                            logger.warning(f"Não consegui restaurar botão Abrir Ticket em canal {channel_id}: {e}")

        tickets_abertos = self.tickets_collection.find({"status": "aberto"})
        for ticket in tickets_abertos:
            guild = self.bot.get_guild(int(ticket["guild_id"]))
            channel = guild.get_channel(ticket["channel_id"]) if guild else None
            if channel:
                try:
                    async for msg in channel.history(limit=50):
                        if msg.author == self.bot.user and msg.embeds:
                            await msg.edit(view=TicketControlView(self.bot, self.tickets_collection, ticket["user_id"]))
                            break
                    logger.info(f"✅ Restaurados botões Claim/Close em {channel.name}")
                except Exception as e:
                    logger.warning(f"Não consegui restaurar Claim/Close em {channel.id}: {e}")

def setup(bot):
    bot.add_cog(TicketSystem(bot))
