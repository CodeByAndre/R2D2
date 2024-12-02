import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View, Select
import random

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reset_game()

    def reset_game(self):
        self.player1 = None
        self.player2 = None
        self.turn = None
        self.gameOver = True
        self.board = ["⬜"] * 9
        self.count = 0
        self.row_messages = []
        self.turn_message = None
        self.winningConditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6],
            [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]
        ]

    @commands.command()
    async def galo(self, ctx, p2: nextcord.Member = None):
        if not p2:
            await ctx.send("Contra qual jogador queres jogar? Escolhe da lista abaixo:")
            members = [m for m in ctx.guild.members if m != self.bot.user and not m.bot]
            options = [nextcord.SelectOption(label=m.name, value=str(m.id)) for m in members]

            select = Select(placeholder="Escolhe um jogador", options=options)

            async def select_callback(interaction: nextcord.Interaction):
                selected_id = int(select.values[0])
                self.player2 = ctx.guild.get_member(selected_id)

                await interaction.response.send_message(f"A perguntar a {self.player2.mention} se aceita jogar...", delete_after=2)
                await self.ask_player(ctx, self.player2)

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
                self.reset_game()
            else:
                await interaction.response.send_message("Apenas o jogador convidado pode responder.", ephemeral=True, delete_after=2)

        buttons[0].callback = accept_callback
        buttons[1].callback = reject_callback

        view = View()
        for button in buttons:
            view.add_item(button)
        await player2.send(f"{ctx.author.mention} convidou-te para jogar Jogo do galo. Aceitas?", view=view)


    async def start_game(self, ctx, player1, player2):
        if self.gameOver:
            self.reset_game()
            self.player1 = player1
            self.player2 = player2
            self.turn = random.choice([self.player1, self.player2])
            self.gameOver = False

            embed = nextcord.Embed(
                title="Jogo da Velha - Tic Tac Toe",
                description=f"É a tua vez {self.turn.mention}!",
                color=nextcord.Color.blurple()
            )
            self.turn_message = await ctx.send(embed=embed)

            self.row_messages = []
            for row_index in range(3):
                view = self.create_row_view(ctx, row_index)
                message = await ctx.send(view=view)
                self.row_messages.append(message)
        else:
            await ctx.send("Um jogo já está em andamento. Termine ou cancele o jogo atual para começar outro.")

    @commands.command()
    async def stopgalo(self, ctx):
        if not self.gameOver:
            await ctx.send(f"{ctx.author.mention} cancelou o jogo.", delete_after=2)
            self.reset_game()
        else:
            await ctx.send("Não há jogo em andamento para cancelar.", delete_after=2)

    def create_row_view(self, ctx, row_index):
        view = View(timeout=None)
        start = row_index * 3
        for i in range(start, start + 3):
            button = Button(
                label=self.board[i],
                style=nextcord.ButtonStyle.success if self.board[i] != "⬜" else nextcord.ButtonStyle.secondary,
                custom_id=str(i),
                disabled=self.board[i] != "⬜"
            )
            button.callback = self.make_move(ctx, i)
            view.add_item(button)
        return view

    def make_move(self, ctx, position):
        async def callback(interaction: nextcord.Interaction):
            if self.gameOver:
                await interaction.response.send_message("O jogo terminou. Comece um novo jogo com `/galo`.", ephemeral=True)
                return

            if interaction.user != self.turn:
                await interaction.response.send_message("Não é a tua vez.", ephemeral=True, delete_after=2)
                return

            if self.board[position] != "⬜":
                await interaction.response.send_message("Essa posição já está ocupada. Escolha outra.", ephemeral=True, delete_after=2)
                return

            mark = "❌" if self.turn == self.player1 else "⭕"
            self.board[position] = mark

            row_index = position // 3
            updated_view = self.create_row_view(ctx, row_index)

            await self.row_messages[row_index].edit(view=updated_view)

            if self.check_winner(mark):
                self.gameOver = True
                embed = nextcord.Embed(
                    title="🏆 Jogo Terminado",
                    description=f"{self.turn.mention} GANHOU!",
                    color=nextcord.Color.green()
                )
                await self.turn_message.edit(embed=embed)
                return

            self.count += 1
            if self.count == 9:
                self.gameOver = True
                embed = nextcord.Embed(
                    title="🏳️ Jogo Terminado",
                    description="Empate!",
                    color=nextcord.Color.yellow()
                )
                await self.turn_message.edit(embed=embed)
                return

            self.turn = self.player1 if self.turn == self.player2 else self.player2
            embed = nextcord.Embed(
                title="Jogo do Galo - Tic Tac Toe",
                description=f"É a tua vez {self.turn.mention}!",
                color=nextcord.Color.blurple()
            )
            await self.turn_message.edit(embed=embed)

        return callback

    def check_winner(self, mark):
        for condition in self.winningConditions:
            if all(self.board[i] == mark for i in condition):
                return True
        return False

def setup(bot):
    bot.add_cog(TicTacToe(bot))
