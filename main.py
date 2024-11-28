import os
import logging
from itertools import cycle
from cryptography.fernet import Fernet
from pymongo import MongoClient
from nextcord.ext import commands, tasks
from dotenv import load_dotenv
import nextcord

load_dotenv()

def load_encryption_key():
    try:
        with open("encryption_key.key", "rb") as key_file:
            return key_file.read()
    except FileNotFoundError:
        raise FileNotFoundError("Ficheiro 'encryption_key.key' não encontrado. Certifique-se de que ele existe.")

key = load_encryption_key()
cipher = Fernet(key)

def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise ValueError("Variável de ambiente 'MONGO_URI' não configurada.")
    return MongoClient(mongo_uri)

client = get_mongo_client()
db = client["R2D2BotDB"]
collection_keys = db["keys"]
collection_prefixes = db["prefixes"]

def get_discord_token():
    token_doc = collection_keys.find_one({"name": "discord_token"})
    if not token_doc:
        raise ValueError("Discord token não encontrado na base de dados!")
    encrypted_token = token_doc["value"]
    return cipher.decrypt(encrypted_token.encode()).decode()

async def get_prefix(bot, message):
    if not message.guild:
        return "/"
    prefix_entry = collection_prefixes.find_one({"server_id": message.guild.id})
    return prefix_entry["prefix"] if prefix_entry else "/"

try:
    token = get_discord_token()
except Exception as e:
    print(f"Erro ao obter o token: {e}")
    exit()

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

client_status = cycle(['🔍 Pesquisas', '🤖 AI', '/help'])

class DiscordLogHandler(logging.Handler):
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    def emit(self, record):
        log_entry = self.format(record)
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"Failed to send log to channel {self.channel_id}. Channel not found.")
            return
        try:
            self.bot.loop.create_task(channel.send(log_entry))
        except Exception as e:
            print(f"Error sending log to Discord channel: {e}")

logger = logging.getLogger("DiscordBot")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("bot.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(file_handler)

discord_handler = DiscordLogHandler(bot, channel_id=1311749142401519616)
discord_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(discord_handler)

@tasks.loop(seconds=10)
async def change_status():
    await bot.change_presence(activity=nextcord.Game(next(client_status)))

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}!")
    logger.info(f"Bot conectado como {bot.user}!")
    await bot.sync_application_commands()
    change_status.start()

@bot.event
async def on_command(ctx):
    logger.info(f"Command '{ctx.command}' used by {ctx.author} in {ctx.guild.name}#{ctx.channel.name}")

@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Error in command '{ctx.command}': {error}")

@bot.event
async def on_guild_join(guild):
    logger.info(f"Adicionado ao servidor {guild.name}. Prefixo padrão configurado para '/'.")
    if not collection_prefixes.find_one({"server_id": guild.id}):
        collection_prefixes.insert_one({"server_id": guild.id, "prefix": "/"})


def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Cog {filename} carregado com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar o cog {filename}: {e}")

    for filename in os.listdir("./admcogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"admcogs.{filename[:-3]}")
                print(f"Admin Cog {filename} carregado com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar o admin cog {filename}: {e}")

load_cogs()

try:
    bot.run(token)
except Exception as e:
    logger.critical(f"Erro ao iniciar o bot: {e}")
