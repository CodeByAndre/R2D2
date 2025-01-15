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

logger = logging.getLogger("DiscordBot")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(file_handler)

@tasks.loop(seconds=10)
async def change_status():
    await bot.change_presence(activity=nextcord.Game(next(client_status)))

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}!")
    logger.info(f"Bot conectado como {bot.user}!")

    try:
        registered_commands = await bot.tree.fetch_commands()
        for command in registered_commands:
            print(f"Comando registrado: {command.name}")
            logger.info(f"Comando registrado: {command.name}")
    except Exception as e:
        print(f"Erro ao listar comandos registrados: {e}")
        logger.error(f"Erro ao listar comandos registrados: {e}")

    try:
        await bot.tree.sync()
        print("Comandos slash sincronizados com sucesso!")
        logger.info("Comandos slash sincronizados com sucesso!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos slash: {e}")
        logger.error(f"Erro ao sincronizar comandos slash: {e}")

    collection_reboot = db["reboot_status"]
    reboot_status = collection_reboot.find_one({"_id": "reboot_status"})

    if reboot_status:
        channel_id = reboot_status.get("channel_id")
        message_id = reboot_status.get("message_id")

        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    if message_id:
                        try:
                            msg = await channel.fetch_message(message_id)
                            await msg.delete()
                            logger.info(f"Deleted the reboot message with ID {message_id} in channel {channel_id}.")
                        except Exception as e:
                            logger.warning(f"Could not delete reboot message with ID {message_id}: {e}")
                    
                    await channel.send("🔄 Reboot completed successfully!", delete_after=5)
                    logger.info(f"Reboot message sent to channel ID {channel_id}.")
                except Exception as e:
                    logger.error(f"Failed to send reboot message or delete old message: {e}")
        else:
            logger.warning("Reboot status found but channel_id is missing.")

        collection_reboot.delete_one({"_id": "reboot_status"})
        logger.info("Reboot status cleared from the database.")

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
                logger.info(f"Cog {filename} carregado com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar o cog {filename}: {e}")
                logger.error(f"Erro ao carregar o cog {filename}: {e}")

    for filename in os.listdir("./admcogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"admcogs.{filename[:-3]}")
                print(f"Admin Cog {filename} carregado com sucesso!")
                logger.info(f"Admin Cog {filename} carregado com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar o admin cog {filename}: {e}")
                logger.error(f"Erro ao carregar o admin cog {filename}: {e}")

load_cogs()

try:
    bot.run(token)
except Exception as e:
    logger.critical(f"Erro ao iniciar o bot: {e}")