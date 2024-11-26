import nextcord
from nextcord.ext import commands
import requests
from pymongo import MongoClient
import os

class FilmesESeries(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["keys"]

        # Fetch API key from the database
        api_key_entry = self.collection.find_one({"name": "TMDB_API_KEY"})
        if not api_key_entry or "value" not in api_key_entry:
            raise ValueError("API key for TMDb not found in the database.")
        self.api_key = api_key_entry["value"]

    @commands.command(name="filme")
    async def filme(self, ctx, *, nome):
        """Fetches movie details from TMDb."""
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={self.api_key}&query={nome}"
        response = requests.get(search_url)

        if response.status_code != 200:
            await ctx.send(f"Erro ao buscar filme: {response.status_code}")
            return

        data = response.json()
        if data["results"]:
            movie_id = data["results"][0]["id"]

            details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={self.api_key}"
            details_response = requests.get(details_url)

            if details_response.status_code != 200:
                await ctx.send(f"Erro ao buscar detalhes do filme: {details_response.status_code}")
                return

            details = details_response.json()

            embed = nextcord.Embed(title=details["title"], color=nextcord.Color.blue())
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{details['poster_path']}")

            embed.add_field(name="Ano", value=details["release_date"].split("-")[0], inline=True)
            embed.add_field(name="Gênero", value=", ".join([genre["name"] for genre in details["genres"]]), inline=True)
            embed.add_field(name="Classificação IMDb", value=details["vote_average"], inline=True)
            embed.add_field(name="Duração", value=f"{details['runtime']} minutos", inline=True)

            watch_url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={self.api_key}"
            watch_response = requests.get(watch_url)

            if watch_response.status_code != 200:
                await ctx.send(f"Erro ao buscar plataformas: {watch_response.status_code}")
                return

            watch_data = watch_response.json()

            if "results" in watch_data and "US" in watch_data["results"]:
                platforms = watch_data["results"]["US"].get("flatrate", [])
                if platforms:
                    platform_names = [platform["provider_name"] for platform in platforms]
                    embed.add_field(name="Onde Assistir", value=", ".join(platform_names), inline=False)
                else:
                    embed.add_field(name="Onde Assistir", value="Não encontrado.", inline=False)
            else:
                embed.add_field(name="Onde Assistir", value="Não disponível ou informação não encontrada.", inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Não encontrei informações sobre o filme '{nome}'. Tente usar o nome completo ou em inglês.")

    @commands.command()
    async def serie(self, ctx, *, nome):
        """Fetches TV series information from TMDb."""
        search_url = f"https://api.themoviedb.org/3/search/tv?api_key={self.api_key}&query={nome}"
        response = requests.get(search_url)

        if response.status_code != 200:
            await ctx.send(f"Erro ao buscar série: {response.status_code}")
            return

        data = response.json()

        if data["results"]:
            series_id = data["results"][0]["id"]

            details_url = f"https://api.themoviedb.org/3/tv/{series_id}?api_key={self.api_key}"
            details_response = requests.get(details_url)
            
            if details_response.status_code != 200:
                await ctx.send(f"Erro ao buscar detalhes da série: {details_response.status_code}")
                return

            details = details_response.json()

            embed = nextcord.Embed(title=details["name"], color=nextcord.Color.green())
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{details['poster_path']}")

            embed.add_field(name="Ano", value=details["first_air_date"].split("-")[0], inline=True)
            embed.add_field(name="Gênero", value=", ".join([genre["name"] for genre in details["genres"]]), inline=True)
            embed.add_field(name="Classificação TMDb", value=details["vote_average"], inline=True)

            # Check if episode_run_time has data
            if details["episode_run_time"]:
                embed.add_field(name="Duração", value=f"{details['episode_run_time'][0]} minutos por episódio", inline=True)
            else:
                embed.add_field(name="Duração", value="Informação não disponível", inline=True)

            watch_url = f"https://api.themoviedb.org/3/tv/{series_id}/watch/providers?api_key={self.api_key}"
            watch_response = requests.get(watch_url)
            
            if watch_response.status_code != 200:
                await ctx.send(f"Erro ao buscar plataformas: {watch_response.status_code}")
                return

            watch_data = watch_response.json()

            if "results" in watch_data and "US" in watch_data["results"]:
                platforms = watch_data["results"]["US"].get("flatrate", [])
                if platforms:
                    platform_names = [platform["provider_name"] for platform in platforms]
                    embed.add_field(name="Onde Assistir", value=", ".join(platform_names), inline=False)
                else:
                    embed.add_field(name="Onde Assistir", value="Não encontrado.", inline=False)
            else:
                embed.add_field(name="Onde Assistir", value="Não disponível ou informação não encontrada.", inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Não encontrei informações sobre a série '{nome}'. Tente usar o nome completo ou em inglês.")


def setup(bot):
    bot.add_cog(FilmesESeries(bot))
