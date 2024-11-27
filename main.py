import os
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

@tasks.loop(seconds=10)
async def change_status():
    await bot.change_presence(activity=nextcord.Game(next(client_status)))

@bot.event
async def on_ready():
    await bot.sync_application_commands()
    print(f"Bot conectado como {bot.user}!")
    
    change_status.start()

    collection_reboot = db["reboot_status"]
    reboot_status = collection_reboot.find_one({"_id": "reboot_status"})
    if reboot_status:
        channel_id = reboot_status.get("channel_id")
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send("Reboot completed successfully!")
        collection_reboot.delete_one({"_id": "reboot_status"})

@bot.event
async def on_guild_join(guild):
    if not collection_prefixes.find_one({"server_id": guild.id}):
        collection_prefixes.insert_one({"server_id": guild.id, "prefix": "/"})
    print(f"Adicionado ao servidor {guild.name} com prefixo padrão '/'.")

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
    print(f"Erro ao iniciar o bot: {e}")
