import os
import threading
import discord
from discord.ext import commands
from flask import Flask

# Inicializa o bot do Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# Função para rodar o bot em uma thread separada
def run_discord_bot():
    bot.run(os.getenv("DISCORD_TOKEN"))

# Cria um servidor Flask apenas para manter o Cloud Run ativo
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot do Discord está rodando!"

# Inicia o bot e o servidor Flask simultaneamente
if __name__ == "__main__":
    threading.Thread(target=run_discord_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
