import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, Select
import random


class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # Stores game states by channel ID or unique keys

    def reset_game(self, channel_id):
        if channel_id in self.games:
            del self.games[channel_id]

    @commands.command()
    async def galo(self, ctx, p2: nextcord.Member = None):
        channel_id = ctx.channel.id
        if channel_id in self.games:
            await ctx.send("Um jogo já está em andamento neste canal. Termine ou cancele o jogo atual.")
            return

        if not p2:
            await ctx.send("Contra qual jogador queres jogar? Escolhe da lista abaixo:")

            members = [m for m in ctx.guild.members if m != self.bot.user and not m.bot]
            if not members:
                await ctx.send("❌ Não há jogadores disponíveis para jogar.")
                return

            members = members[:25]
            options = [nextcord.SelectOption(label=m.name, value=str(m.id)) for m in members]

            select = Select(placeholder="Escolhe um jogador", options=options)

            async def select_callback(interaction: nextcord.Interaction):
                selected_id = int(select.values[0])
                selected_member = ctx.guild.get_member(selected_id)
                await interaction.response.send_message(f"A perguntar a {selected_member.mention} se aceita jogar...", delete_after=2)
                await self.ask_player(ctx, selected_member)

            select.callback = select_callback
            view = View(timeout=30)
            view.add_item(select)
            await ctx.send(view=view)
            return

        if p2 == self.bot.user:
            await ctx.send("❌ Não podes jogar contra mim!", delete_after=2)
            return

        await ctx.send(f"A perguntar a {p2.mention} se aceita jogar...", delete_after=2)
        await self.ask_player(ctx, p2)

    async def ask_player(self, ctx, player2):
        buttons = [
            Button(label="Aceitar", style=nextcord.ButtonStyle.success),
            Button(label="Recusar", style=nextcord.ButtonStyle.danger)
        ]

        async def accept_callback(interaction: nextcord.Interaction):
            if interaction.user == player2:
                await interaction.response.send_message("Jogo aceito! O jogo vai começar.", ephemeral=True)
                await self.start_game(ctx, ctx.author, player2)
            else:
                await interaction.response.send_message("Apenas o jogador convidado pode responder.", ephemeral=True, delete_after=2)

        async def reject_callback(interaction: nextcord.Interaction):
            if interaction.user == player2:
                await interaction.response.send_message("Jogo recusado.", ephemeral=True, delete_after=2)
                self.reset_game(ctx.channel.id)
            else:
                await interaction.response.send_message("Apenas o jogador convidado pode responder.", ephemeral=True, delete_after=2)

        buttons[0].callback = accept_callback
        buttons[1].callback = reject_callback

        view = View()
        for button in buttons:
            view.add_item(button)
        await player2.send(f"{ctx.author.mention} convidou-te para jogar Jogo do Galo. Aceitas?", view=view)

    async def start_game(self, ctx, player1, player2):
        channel_id = ctx.channel.id
        self.games[channel_id] = {
            "player1": player1,
            "player2": player2,
            "turn": random.choice([player1, player2]),
            "board": ["⬜"] * 9,
            "count": 0,
            "row_messages": [],
            "turn_message": None,
            "gameOver": False
        }

        game = self.games[channel_id]

        embed = nextcord.Embed(
            title="Jogo do Galo - Tic Tac Toe",
            description=f"É a tua vez {game['turn'].mention}!",
            color=nextcord.Color.blurple()
        )
        game["turn_message"] = await ctx.send(embed=embed)

        for row_index in range(3):
            view = self.create_row_view(ctx, channel_id, row_index)
            message = await ctx.send(view=view)
            game["row_messages"].append(message)

    def create_row_view(self, ctx, channel_id, row_index):
        game = self.games[channel_id]
        view = View(timeout=None)
        start = row_index * 3
        for i in range(start, start + 3):
            button = Button(
                label=game["board"][i],
                style=nextcord.ButtonStyle.success if game["board"][i] != "⬜" else nextcord.ButtonStyle.secondary,
                custom_id=str(i),
                disabled=game["board"][i] != "⬜"
            )
            button.callback = self.make_move(ctx, channel_id, i)
            view.add_item(button)
        return view

    def make_move(self, ctx, channel_id, position):
        async def callback(interaction: nextcord.Interaction):
            game = self.games[channel_id]

            if game["gameOver"]:
                await interaction.response.send_message("O jogo terminou. Comece um novo jogo com `/galo`.", ephemeral=True)
                return

            if interaction.user != game["turn"]:
                await interaction.response.send_message("Não é a tua vez.", ephemeral=True, delete_after=2)
                return

            if game["board"][position] != "⬜":
                await interaction.response.send_message("Essa posição já está ocupada. Escolha outra.", ephemeral=True, delete_after=2)
                return

            mark = "❌" if game["turn"] == game["player1"] else "⭕"
            game["board"][position] = mark

            row_index = position // 3
            updated_view = self.create_row_view(ctx, channel_id, row_index)
            await game["row_messages"][row_index].edit(view=updated_view)

            if self.check_winner(game["board"], mark):
                game["gameOver"] = True
                embed = nextcord.Embed(
                    title="🏆 Jogo Terminado",
                    description=f"{game['turn'].mention} GANHOU!",
                    color=nextcord.Color.green()
                )
                await game["turn_message"].edit(embed=embed)
                self.reset_game(channel_id)
                return

            game["count"] += 1
            if game["count"] == 9:
                game["gameOver"] = True
                embed = nextcord.Embed(
                    title="🏳️ Jogo Terminado",
                    description="Empate!",
                    color=nextcord.Color.yellow()
                )
                await game["turn_message"].edit(embed=embed)
                self.reset_game(channel_id)
                return

            game["turn"] = game["player1"] if game["turn"] == game["player2"] else game["player2"]
            embed = nextcord.Embed(
                title="Jogo do Galo - Tic Tac Toe",
                description=f"É a tua vez {game['turn'].mention}!",
                color=nextcord.Color.blurple()
            )
            await game["turn_message"].edit(embed=embed)

        return callback

    def check_winner(self, board, mark):
        winning_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        return any(all(board[i] == mark for i in condition) for condition in winning_conditions)


def setup(bot):
    bot.add_cog(TicTacToe(bot))
