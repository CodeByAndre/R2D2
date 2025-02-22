import nextcord
from nextcord.ext import commands
from nextcord import File, Interaction, SlashOption
from easy_pil import Editor, load_image_async, Font
from pymongo import MongoClient
import os

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["welcome_channels"]

    @commands.Cog.listener()
    async def on_member_join(self, member: nextcord.Member):
        try:
            channel_data = self.collection.find_one({"server_id": member.guild.id})
            channel_id = channel_data.get("channel_id") if channel_data else None
            channel = member.guild.get_channel(channel_id) if channel_id else member.guild.system_channel

            if channel is None:
                print("Nenhum canal configurado ou system channel não definido.")
                return

            server_name = member.guild.name
            max_length = 11
            if len(server_name) > max_length:
                server_name = server_name[:max_length] + "..."

            if not server_name.strip():
                server_name = "este servidor"

            background = Editor("pic2.jpg")
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url

            profile_image = await load_image_async(str(avatar_url))
            profile = Editor(profile_image).resize((150, 150)).circle_image()

            poppins = Font.poppins(size=50, variant="bold")
            poppins_small = Font.poppins(size=20, variant="light")

            background.paste(profile, (325, 90))
            background.ellipse((325, 90), 150, 150, outline="white", stroke_width=5)

            background.text((400, 260), f"BEM-VINDO AO {server_name}", color="white", font=poppins, align="center")
            background.text((400, 325), f"{member.name}#{member.discriminator}", color="black", font=poppins_small, align="center")

            file = File(fp=background.image_bytes, filename="welcome.jpg")

            await channel.send(f"OLÁ! {member.mention}! BEM-VINDO ao **{server_name}**. Para mais informações lê o canal das regras.")
            await channel.send(file=file)
            
        except Exception as e:
            print(f"❌ An error occurred: {e}")

    @nextcord.slash_command(name="setwelcome", description="Configura o canal de boas-vindas.")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(
        self,
        interaction: Interaction,
        channel: nextcord.TextChannel = SlashOption(
            name="canal",
            description="Mencione o canal de boas-vindas.",
            required=True
        )
    ):
        try:
            self.collection.update_one(
                {"server_id": interaction.guild.id},
                {"$set": {"channel_id": channel.id}},
                upsert=True
            )
            await interaction.response.send_message(f"✅ O canal de boas-vindas foi configurado para {channel.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu um erro ao salvar o canal de boas-vindas: {e}")

    @set_welcome_channel.error
    async def set_welcome_channel_error(self, interaction: Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("❌ Apenas administradores podem usar este comando.", ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await interaction.response.send_message("❌ Por favor, mencione um canal válido.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ocorreu um erro ao processar o comando.", ephemeral=True)

def setup(bot):
    bot.add_cog(Welcome(bot))