import nextcord
from nextcord.ext import commands
from pymongo import MongoClient
import random
import os

class Futebolada(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["players"]

    @commands.command()
    async def player(self, ctx, *args):
        """Adds players with skills to the database."""
        if len(args) % 2 != 0:
            await ctx.send("Por favor, forneça pares de nome e habilidade (exemplo: `Lukas bom Pedro medio`).")
            return

        guild_id = str(ctx.guild.id)
        added_players = []

        for i in range(0, len(args), 2):
            name = args[i]
            skill = args[i + 1].lower()
            if skill not in ["bom", "medio", "mau"]:
                await ctx.send(f"Habilidade inválida para {name}: {skill}. Use 'bom', 'medio', ou 'mau'.")
                return

            self.collection.update_one(
                {"guild_id": guild_id, "name": name},
                {"$set": {"skill": skill}},
                upsert=True
            )
            added_players.append(f"{name} ({skill})")

        await ctx.send(f"Jogadores adicionados: {', '.join(added_players)}")

    @commands.command()
    async def rplayer(self, ctx, name: str):
        """Removes a player from the database."""
        guild_id = str(ctx.guild.id)
        result = self.collection.delete_one({"guild_id": guild_id, "name": name})
        if result.deleted_count > 0:
            await ctx.send(f"{name} removido da lista de jogadores.")
        else:
            await ctx.send(f"{name} não encontrado na lista de jogadores.")

    @commands.command()
    async def players(self, ctx):
        """Displays the list of players and their skills."""
        guild_id = str(ctx.guild.id)
        players = list(self.collection.find({"guild_id": guild_id}))

        if not players:
            await ctx.send("❌ Não há jogadores registrados para este servidor.")
            return

        skill_emojis = {
            "bom": "🌟 Bom",
            "medio": "⚖️ Médio",
            "mau": "👎 Mau"
        }

        embed = nextcord.Embed(
            title="🏆 Lista de Jogadores",
            description="Aqui estão os jogadores registrados para este servidor.",
            color=nextcord.Color.blue()
        )

        for player in players:
            embed.add_field(name=f"👤 {player['name']}", value=skill_emojis.get(player["skill"], player["skill"]), inline=True)

        embed.set_footer(text=f"Total de jogadores: {len(players)}")
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)

    @commands.command()
    async def clearp(self, ctx):
        """Clears all players for the current server."""
        guild_id = str(ctx.guild.id)
        result = self.collection.delete_many({"guild_id": guild_id})
        if result.deleted_count > 0:
            await ctx.send("✅ Todos os jogadores foram removidos da lista!")
        else:
            await ctx.send("❌ Não há jogadores registrados para este servidor.")

    @commands.command()
    async def futebolada(self, ctx):
        """Creates two balanced teams from the registered players."""
        guild_id = str(ctx.guild.id)
        players = list(self.collection.find({"guild_id": guild_id}))

        if len(players) < 4:
            await ctx.send("Por favor, adicione pelo menos 4 jogadores com habilidades.")
            return

        skill_groups = {"bom": [], "medio": [], "mau": []}
        for player in players:
            skill_groups[player["skill"]].append(player["name"])

        balanced_teams = self.balance_teams(skill_groups)

        embed = nextcord.Embed(title="Equipas da Futebolada", color=nextcord.Color.green())
        embed.add_field(
            name="EQUIPA 1",
            value="\n".join(balanced_teams["team_1"]),
            inline=True
        )
        embed.add_field(
            name="EQUIPA 2",
            value="\n".join(balanced_teams["team_2"]),
            inline=True
        )

        await ctx.send(embed=embed)

    def balance_teams(self, skill_groups):
        """Balances teams based on player skills."""
        random.shuffle(skill_groups["bom"])
        random.shuffle(skill_groups["medio"])
        random.shuffle(skill_groups["mau"])

        team_1, team_2 = [], []

        def distribute_evenly(team_1, team_2, player_list):
            for i, player in enumerate(player_list):
                if len(team_1) <= len(team_2):
                    team_1.append(player)
                else:
                    team_2.append(player)

        distribute_evenly(team_1, team_2, skill_groups["bom"])
        distribute_evenly(team_1, team_2, skill_groups["medio"])
        distribute_evenly(team_1, team_2, skill_groups["mau"])

        while abs(len(team_1) - len(team_2)) > 1:
            if len(team_1) > len(team_2):
                team_2.append(team_1.pop())
            else:
                team_1.append(team_2.pop())

        return {"team_1": team_1, "team_2": team_2}

def setup(bot):
    bot.add_cog(Futebolada(bot))
