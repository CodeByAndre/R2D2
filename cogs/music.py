import os
from dotenv import load_dotenv
from pymongo import MongoClient
import nextcord
from nextcord.ext import commands
from nextcord import FFmpegPCMAudio, Embed, Interaction
from nextcord.ui import View, Button
import yt_dlp as ytdl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import asyncio

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI não encontrado no arquivo .env!")

client = MongoClient(MONGO_URI)
db = client["R2D2BotDB"]
collection = db["keys"]

def get_spotify_credentials():
    try:
        credentials = collection.find_one({"name": "spotify"})
        if not credentials:
            print("⚠️ Credenciais do Spotify não encontradas na coleção 'keys'!")
            return None, None
        return credentials["client_id"], credentials["client_secret"]
    except Exception as e:
        print(f"Erro ao buscar credenciais do Spotify: {e}")
        return None, None

SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET = get_spotify_credentials()

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    print("❌ Credenciais do Spotify não foram carregadas. O recurso do Spotify estará desativado.")
    spotify = None
else:
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

ffmpeg_opts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -reconnect_on_network_error 1',
    'options': '-vn -af "aresample=async=1,loudnorm"'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'keepvideo': False,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '192',
    }],
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

class NowPlayingView(View):
    def __init__(self, music_cog, ctx):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.ctx = ctx

    @nextcord.ui.button(emoji="⏸️", style=nextcord.ButtonStyle.grey)
    async def pause_button(self, button: Button, interaction: nextcord.Interaction):
        if interaction.user != self.ctx.user:
            await interaction.response.send_message("⚠️ Apenas quem iniciou a música pode usar este botão.", ephemeral=True)
            return

        if self.ctx.guild.voice_client and self.ctx.guild.voice_client.is_playing():
            self.ctx.guild.voice_client.pause()
            await interaction.response.send_message("⏸️ Música pausada.", delete_after=2)
        else:
            await interaction.response.send_message("❌ Não há música tocando para pausar.", delete_after=2)

    @nextcord.ui.button(emoji="▶️", style=nextcord.ButtonStyle.grey)
    async def resume_button(self, button: Button, interaction: nextcord.Interaction):
        if interaction.user != self.ctx.user:
            await interaction.response.send_message("⚠️ Apenas quem iniciou a música pode usar este botão.", ephemeral=True)
            return

        if self.ctx.guild.voice_client and self.ctx.guild.voice_client.is_paused():
            self.ctx.guild.voice_client.resume()
            await interaction.response.send_message("▶️ Música retomada.", delete_after=2)
        else:
            await interaction.response.send_message("❌ Não há música pausada para retomar.", delete_after=2)

    @nextcord.ui.button(emoji="⏭️", style=nextcord.ButtonStyle.grey)
    async def skip_button(self, button: Button, interaction: nextcord.Interaction):
        if interaction.user != self.ctx.user:
            await interaction.response.send_message("⚠️ Apenas quem iniciou a música pode usar este botão.", ephemeral=True)
            return

        if self.ctx.guild.voice_client and self.ctx.guild.voice_client.is_playing():
            self.ctx.guild.voice_client.stop()
            await interaction.response.send_message("⏭️ Música pulada.", delete_after=2)
        else:
            await interaction.response.send_message("❌ Não há música tocando para pular.", delete_after=2)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_data = {}

    def get_guild_data(self, guild_id):
        if guild_id not in self.guild_data:
            self.guild_data[guild_id] = {
                "queue": [],
                "is_playing": False,
                "current_ctx": None,
                "now_playing_message": None
            }
        return self.guild_data[guild_id]

    async def fetch_audio_url(self, query):
        try:
            is_url = query.startswith("http")
            search_query = query if is_url else f"ytsearch:{query}"

            with ytdl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if not is_url:
                    info = info['entries'][0]
                audio_url = next((format['url'] for format in info['formats'] if format.get('acodec') != 'none'), None)

                return audio_url, info
        except Exception as e:
            print(f"Error fetching audio URL: {e}")
            return None, None

    async def fetch_spotify_playlist(self, playlist_url):
        try:
            results = spotify.playlist_items(playlist_url)
            tracks = results["items"]
            songs = []

            for track in tracks:
                track_name = track["track"]["name"]
                artist_name = track["track"]["artists"][0]["name"]
                songs.append(f"{artist_name} - {track_name}")

            return songs
        except Exception as e:
            print(f"Erro ao buscar playlist do Spotify: {e}")
            return None

    async def play_song(self, interaction: Interaction, query):
        guild_data = self.get_guild_data(interaction.guild.id)
        if not interaction.guild.voice_client:
            await interaction.followup.send("❌ O bot não está conectado a um canal de voz.", delete_after=5)
            guild_data["is_playing"] = False
            return

        if not guild_data.get("now_playing_message"):
            message = await interaction.followup.send("🔍 A procura da música, aguarde...")
            guild_data["now_playing_message"] = message
        else:
            message = guild_data["now_playing_message"]

        audio_url, info = await self.fetch_audio_url(query)

        if audio_url and info:
            audio_source = FFmpegPCMAudio(audio_url, **ffmpeg_opts)
            interaction.guild.voice_client.play(
                audio_source,
                after=lambda e: asyncio.run_coroutine_threadsafe(self.handle_song_end(interaction), self.bot.loop)
            )

            guild_data["current_ctx"] = interaction

            embed = Embed(
                title="🎵 Now Playing",
                description=info['title'],
                color=nextcord.Color.blue()
            )
            embed.add_field(name="Duração", value=info.get('duration', 'N/A'), inline=True)
            embed.add_field(name="URL", value=f"[Clique aqui para assistir]({info['webpage_url']})", inline=True)
            if 'thumbnail' in info:
                embed.set_thumbnail(url=info['thumbnail'])

            view = NowPlayingView(self, interaction)

            await message.edit(content=None, embed=embed, view=view)
        else:
            await message.edit(content="❌ Não foi possível encontrar a música.")
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.disconnect()
            guild_data["is_playing"] = False

    async def handle_song_end(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        if guild_data["queue"]:
            next_song = guild_data["queue"].pop(0)
            await self.play_song(ctx, next_song[0])
        else:
            guild_data["is_playing"] = False
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            await ctx.send("✅ A fila de músicas acabou. Desconectando...", delete_after=5)

    @nextcord.slash_command(name="play", description="Toca uma música ou playlist")
    async def play(self, interaction: Interaction, *, query: str):
        guild_data = self.get_guild_data(interaction.guild.id)

        if not interaction.user.voice:
            await interaction.response.send_message("❌ Precisas de estar em um canal de voz!", delete_after=5)
            return

        if not interaction.guild.voice_client:
            await interaction.user.voice.channel.connect()

        message = await interaction.response.send_message("🔍 A buscar músicas na playlist do Spotify...")

        if "spotify.com/playlist" in query:
            songs = await self.fetch_spotify_playlist(query)
            if not songs:
                await message.edit(content="❌ Não foi possível obter a playlist do Spotify.")
                return
            for song in songs:
                guild_data["queue"].append((song, None))
            await message.edit(content=f"✅ Playlist adicionada com {len(songs)} músicas!")
            if not guild_data["is_playing"]:
                guild_data["is_playing"] = True
                await self.play_song(interaction, guild_data["queue"].pop(0)[0])
        else:
            if not guild_data["is_playing"]:
                guild_data["is_playing"] = True
                await self.play_song(interaction, query)
            else:
                audio_url, info = await self.fetch_audio_url(query)
                if audio_url and info:
                    guild_data["queue"].append((query, info))
                    embed = Embed(
                        title="🎵 Música adicionada à fila",
                        description=f"[{info['title']}]({info['webpage_url']})",
                        color=nextcord.Color.purple()
                    )
                    await message.edit(embed=embed)
                else:
                    await message.edit(content="❌ Não foi possível adicionar a música.")

    @nextcord.slash_command(name="queue", description="Exibe a fila de músicas")
    async def queue(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        if not guild_data["queue"]:
            await ctx.send("❌ A fila está vazia.", delete_after=5)
        else:
            embed = Embed(title="🎵 Fila de músicas", color=nextcord.Color.green())
            for i, (query, info) in enumerate(guild_data["queue"], start=1):
                if info:
                    embed.add_field(name=f"{i}. {info['title']}", value=f"[Ouvir aqui]({info['webpage_url']})", inline=False)
                else:
                    embed.add_field(name=f"{i}. {query}", value="Adicionado da playlist do Spotify", inline=False)
            await ctx.send(embed=embed)

    @nextcord.slash_command(name="stop", description="Para a música e limpa a fila")
    async def stop(self, interaction: Interaction):
        guild_data = self.get_guild_data(interaction.guild.id)
        voice_client = interaction.guild.voice_client

        if voice_client:
            voice_client.stop()
            guild_data["queue"].clear()
            guild_data["is_playing"] = False
            await voice_client.disconnect()
            await interaction.response.send_message("🛑 Música parada e desconectado do canal de voz.", delete_after=5)
        else:
            await interaction.response.send_message("❌ O bot não está tocando música.", delete_after=5)

def setup(bot):
    bot.add_cog(Music(bot))