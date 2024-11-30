import nextcord
from nextcord.ext import commands
from nextcord import FFmpegPCMAudio, Embed
from nextcord.ui import View, Button
import yt_dlp as ytdl
import asyncio

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
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("⚠️ Apenas quem iniciou a música pode usar este botão.", ephemeral=True)
            return

        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            await interaction.response.send_message("⏸️ Música pausada.", delete_after=2)
        else:
            await interaction.response.send_message("❌ Não há música tocando para pausar.", delete_after=2)

    @nextcord.ui.button(emoji="▶️", style=nextcord.ButtonStyle.green)
    async def resume_button(self, button: Button, interaction: nextcord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("⚠️ Apenas quem iniciou a música pode usar este botão.", ephemeral=True)
            return

        if self.ctx.voice_client and self.ctx.voice_client.is_paused():
            self.ctx.voice_client.resume()
            await interaction.response.send_message("▶️ Música retomada.", delete_after=2)
        else:
            await interaction.response.send_message("❌ Não há música pausada para retomar.", delete_after=2)

    @nextcord.ui.button(emoji="⏭️", style=nextcord.ButtonStyle.red)
    async def skip_button(self, button: Button, interaction: nextcord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("⚠️ Apenas quem iniciou a música pode usar este botão.", ephemeral=True)
            return

        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
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

    async def play_song(self, ctx, query):
        guild_data = self.get_guild_data(ctx.guild.id)
        if not ctx.voice_client:
            await ctx.send("❌ O bot não está conectado a um canal de voz.", delete_after=5)
            guild_data["is_playing"] = False
            return

        search_msg = await ctx.send("🔍 A procura da música, aguarde...")
        audio_url, info = await self.fetch_audio_url(query)

        if audio_url and info:
            audio_source = FFmpegPCMAudio(audio_url, **ffmpeg_opts)
            ctx.voice_client.play(
                audio_source,
                after=lambda e: asyncio.run_coroutine_threadsafe(self.handle_song_end(ctx), self.bot.loop)
            )

            guild_data["current_ctx"] = ctx
            await search_msg.delete()

            embed = Embed(
                title="🎵 Now Playing",
                description=info['title'],
                color=nextcord.Color.blue()
            )
            embed.add_field(name="Duração", value=info.get('duration', 'N/A'), inline=True)
            embed.add_field(name="URL", value=f"[Clique aqui para assistir]({info['webpage_url']})", inline=True)
            if 'thumbnail' in info:
                embed.set_thumbnail(url=info['thumbnail'])

            view = NowPlayingView(self, ctx)

            if guild_data["now_playing_message"]:
                await guild_data["now_playing_message"].edit(embed=embed, view=view)
            else:
                guild_data["now_playing_message"] = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send("❌ Não foi possível encontrar a música.", delete_after=5)
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            guild_data["is_playing"] = False

    async def handle_song_end(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        if guild_data["queue"]:
            next_song = guild_data["queue"].pop(0)
            await self.play_song(ctx, next_song)
        else:
            guild_data["is_playing"] = False
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            await ctx.send("✅ A fila de músicas acabou. Desconectando...", delete_after=5)

    @commands.command()
    async def play(self, ctx, *, query: str):
        guild_data = self.get_guild_data(ctx.guild.id)

        if not ctx.author.voice:
            await ctx.send("❌ Precisas de estar em um canal de voz!", delete_after=5)
            return

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        if not guild_data["is_playing"]:
            guild_data["is_playing"] = True
            await self.play_song(ctx, query)
        else:
            guild_data["queue"].append(query)
            audio_url, info = await self.fetch_audio_url(query)
            if audio_url and info:
                embed = Embed(
                    title="🎵 Música adicionada à fila",
                    description=f"[{info['title']}]({info['webpage_url']})",
                    color=nextcord.Color.purple()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Não foi possível adicionar a música.", delete_after=5)

    @commands.command()
    async def queue(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        if not guild_data["queue"]:
            await ctx.send("❌ A fila está vazia.", delete_after=5)
        else:
            embed = Embed(title="🎵 Fila de músicas", color=nextcord.Color.green())
            for i, query in enumerate(guild_data["queue"], start=1):
                _, info = await self.fetch_audio_url(query)
                embed.add_field(name=f"{i}. {info['title']}", value=f"[Ouvir aqui]({info['webpage_url']})", inline=False)
            await ctx.send(embed=embed)

    @commands.command()
    async def stop(self, ctx):
        guild_data = self.get_guild_data(ctx.guild.id)
        if ctx.voice_client:
            ctx.voice_client.stop()
            guild_data["queue"].clear()
            guild_data["is_playing"] = False
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Música parada e desconectado do canal de voz.", delete_after=5)
        else:
            await ctx.send("❌ O bot não está tocando música.", delete_after=5)


def setup(bot):
    bot.add_cog(Music(bot))
