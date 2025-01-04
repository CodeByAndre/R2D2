import nextcord
from nextcord.ext import commands
from pymongo import MongoClient
import os
import random
import difflib

class Futebolada(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["R2D2BotDB"]
        self.collection = self.db["players"]

    @commands.command()
    async def player(self, ctx, *args):
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
        guild_id = str(ctx.guild.id)
        result = self.collection.delete_one({"guild_id": guild_id, "name": name})
        if result.deleted_count > 0:
            await ctx.send(f"{name} removido da lista de jogadores.")
        else:
            await ctx.send(f"{name} não encontrado na lista de jogadores.")

    @commands.command()
    async def players(self, ctx):
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
        guild_id = str(ctx.guild.id)
        result = self.collection.delete_many({"guild_id": guild_id})
        if result.deleted_count > 0:
            await ctx.send("✅ Todos os jogadores foram removidos da lista!")
        else:
            await ctx.send("❌ Não há jogadores registrados para este servidor.")

    @commands.command()
    async def futebolada(self, ctx):
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

    @commands.command()
    async def futeboladarandom(self, ctx):
        guild_id = str(ctx.guild.id)
        players = list(self.collection.find({"guild_id": guild_id}))

        if len(players) < 4:
            await ctx.send("Por favor, adicione pelo menos 4 jogadores com habilidades.")
            return

        player_names = [player["name"] for player in players]
        random.shuffle(player_names)

        midpoint = len(player_names) // 2
        team_1 = player_names[:midpoint]
        team_2 = player_names[midpoint:]

        embed = nextcord.Embed(title="Equipas Aleatórias da Futebolada", color=nextcord.Color.orange())
        embed.add_field(
            name="EQUIPA 1",
            value="\n".join(team_1),
            inline=True
        )
        embed.add_field(
            name="EQUIPA 2",
            value="\n".join(team_2),
            inline=True
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def sync_players(self, ctx, *, player_list: str):
        guild_id = str(ctx.guild.id)

        # Parse da lista fornecida pelo usuário
        confirmed_players = []
        for line in player_list.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                name = " ".join(parts[:-1])  # Nome pode ter espaços
                skill = parts[-1].lower()  # Última palavra é a habilidade
                if skill in ["bom", "medio", "mau"]:
                    confirmed_players.append({"name": name, "skill": skill})
                else:
                    await ctx.send(f"Habilidade inválida para {name}: {skill}. Use 'bom', 'medio' ou 'mau'.")
                    return

        # Obter jogadores do banco de dados
        db_players = list(self.collection.find({"guild_id": guild_id}))

        confirmed_names = [player["name"] for player in confirmed_players]
        removed_players = []
        updated_players = []

        # Verificar jogadores na DB
        for db_player in db_players:
            db_name = db_player["name"]
            match = difflib.get_close_matches(db_name, confirmed_names, n=1, cutoff=0.8)
            if not match:
                # Remover da DB se não estiver na lista confirmada
                self.collection.delete_one({"_id": db_player["_id"]})
                removed_players.append(db_name)
            else:
                # Atualizar habilidade se necessário
                confirmed_player = next(
                    (player for player in confirmed_players if player["name"] == match[0]), None
                )
                if confirmed_player and db_player["skill"] != confirmed_player["skill"]:
                    self.collection.update_one(
                        {"_id": db_player["_id"]},
                        {"$set": {"skill": confirmed_player["skill"]}}
                    )
                    updated_players.append(f"{db_name} atualizado para {confirmed_player['skill']}")

        # Adicionar novos jogadores confirmados
        for player in confirmed_players:
            if not any(
                difflib.get_close_matches(player["name"], [p["name"] for p in db_players], n=1, cutoff=0.8)
            ):
                self.collection.insert_one(
                    {"guild_id": guild_id, "name": player["name"], "skill": player["skill"]}
                )
                updated_players.append(f"{player['name']} ({player['skill']}) adicionado")

        # Resumo da sincronização
        embed = nextcord.Embed(
            title="🔄 Sincronização de Jogadores",
            color=nextcord.Color.blue()
        )
        if removed_players:
            embed.add_field(
                name="Jogadores Removidos",
                value="\n".join(removed_players),
                inline=False
            )
        else:
            embed.add_field(name="Jogadores Removidos", value="Nenhum jogador removido.", inline=False)

        if updated_players:
            embed.add_field(
                name="Atualizações/Adições",
                value="\n".join(updated_players),
                inline=False
            )
        else:
            embed.add_field(name="Atualizações/Adições", value="Nenhuma atualização realizada.", inline=False)

        await ctx.send(embed=embed)

    def balance_teams(self, skill_groups):
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
