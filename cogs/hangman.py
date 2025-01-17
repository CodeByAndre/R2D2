import nextcord
from nextcord.ext import commands
import random

class Hangman(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.command(name="hangman")
    async def start_hangman(self, ctx):
        words = ["python", "discord", "hangman", "programming", "challenge"]
        word = random.choice(words)
        guessed = ["_"] * len(word)
        attempts = 6
        tried_letters = []

        self.games[ctx.channel.id] = {
            "word": word,
            "guessed": guessed,
            "attempts": attempts,
            "tried_letters": tried_letters
        }

        await ctx.send(f"Novo jogo da forca iniciado! A palavra tem {len(word)} letras.\n"
                       f"Palavra: {' '.join(guessed)}\n"
                       f"Tentativas restantes: {attempts}\n"
                       f"Letras tentadas: {', '.join(tried_letters)}")

    @commands.command(name="guess")
    async def guess_letter(self, ctx, letter: str):
        if len(letter) != 1 or not letter.isalpha():
            await ctx.send("Por favor, insira uma única letra válida.")
            return

        channel_id = ctx.channel.id
        if channel_id not in self.games:
            await ctx.send("Nenhum jogo da forca em andamento neste canal.")
            return

        game = self.games[channel_id]
        word = game["word"]
        guessed = game["guessed"]
        attempts = game["attempts"]
        tried_letters = game["tried_letters"]

        if letter in tried_letters:
            await ctx.send("Você já tentou esta letra.")
            return

        tried_letters.append(letter)

        if letter in word:
            for i, char in enumerate(word):
                if char == letter:
                    guessed[i] = letter
        else:
            attempts -= 1

        game["attempts"] = attempts
        game["guessed"] = guessed
        game["tried_letters"] = tried_letters

        if "_" not in guessed:
            await ctx.send(f"Parabéns! Você adivinhou a palavra: {word}")
            del self.games[channel_id]
            return

        if attempts == 0:
            await ctx.send(f"Fim de jogo! A palavra era: {word}")
            del self.games[channel_id]
            return

        await ctx.send(f"Palavra: {' '.join(guessed)}\n"
                       f"Tentativas restantes: {attempts}\n"
                       f"Letras tentadas: {', '.join(tried_letters)}")

def setup(bot):
    bot.add_cog(Hangman(bot))