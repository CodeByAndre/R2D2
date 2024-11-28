import nextcord
from nextcord.ext import commands
from nextcord import FFmpegPCMAudio, Embed
from nextcord.ui import View, Button
import yt_dlp as ytdl
import asyncio

ffmpeg_opts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -acodec pcm_s16le -ar 48000 -ac 2'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'noplaylist': True,
    'keepvideo': False,
    'postprocessors': []
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
        self.queue = []
        self.is_playing = False
        self.current_ctx = None
        self.now_playing_message = None

    async def clear_state(self):
        self.queue.clear()
        self.is_playing = False
        self.current_ctx = None
        self.now_playing_message = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user and before.channel is not None and after.channel is None:
            if self.current_ctx:
                try:
                    await self.current_ctx.send("O bot foi desconectado do canal.", delete_after=5)
                except Exception as e:
                    print(f"Error sending disconnect message: {e}")
            await self.clear_state()

    async def fetch_audio_url(self, query):
        try:
            is_url = query.startswith("http")
            search_query = query if is_url else f"ytsearch:{query}"

            with ytdl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(search_query, download=False)
                if not is_url:
                    info = info['entries'][0]
                audio_url = next((format['url'] for format in info['formats'] if format.get('acodec') != 'none'), None)

                if audio_url:
                    return audio_url, info
        except Exception as e:
            print(f"Error fetching audio URL: {e}")
            return None, None

    async def play_song(self, ctx, query):
        if not ctx.voice_client:
            await ctx.send("❌ O bot não está conectado a um canal de voz.", delete_after=5)
            await self.clear_state()
            return

        search_msg = await ctx.send("🔍 A procura da música, aguarde...")
        audio_url, info = await self.fetch_audio_url(query)

        if audio_url and info:
            audio_source = FFmpegPCMAudio(audio_url, **ffmpeg_opts)
            ctx.voice_client.play(audio_source, after=lambda e: self.bot.loop.create_task(self.handle_song_end(ctx)))

            self.current_ctx = ctx
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

            view = NowPlayingView(self, ctx)  # Attach the button controls to the embed

            if self.now_playing_message:
                await self.now_playing_message.edit(embed=embed, view=view)
            else:
                self.now_playing_message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send("❌ Não foi possível encontrar a música.", delete_after=5)
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            await self.clear_state()

    async def handle_song_end(self, ctx):
        if len(self.queue) > 0:
            next_song = self.queue.pop(0)
            await self.play_song(ctx, next_song)
        else:
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            self.is_playing = False
            await ctx.send("✅ A fila de músicas acabou. Desconectando...", delete_after=5)

    @commands.command()
    async def play(self, ctx, *, query: str):
        if not ctx.author.voice:
            await ctx.send("❌ Precisas de estar em um canal de voz!", delete_after=5)
            return

        voice_channel = ctx.author.voice.channel

        if not ctx.voice_client:
            await voice_channel.connect()

        if not self.is_playing:
            self.is_playing = True
            await self.play_song(ctx, query)
        else:
            self.queue.append(query)
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
        if not self.queue:
            await ctx.send("❌ A fila está vazia.", delete_after=5)
        else:
            embed = Embed(title="🎵 Fila de músicas", color=nextcord.Color.green())
            for i, query in enumerate(self.queue, start=1):
                _, info = await self.fetch_audio_url(query)
                embed.add_field(name=f"{i}. {info['title']}", value=f"[Ouvir aqui]({info['webpage_url']})", inline=False)
            await ctx.send(embed=embed)

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Música parada e desconectado do canal de voz.", delete_after=5)
        else:
            await ctx.send("❌ O bot não está tocando música.", delete_after=5)


def setup(bot):
    bot.add_cog(Music(bot))
