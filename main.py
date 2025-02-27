import os
import discord
from discord.ext import commands
from gtts import gTTS
from io import BytesIO
import asyncio
import requests
from flask import Flask
import shutil

# Inicializa um servidor Flask para Cloud Run
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot rodando!"

# Configurações iniciais
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DEEPSEEK_API_KEY:
    raise ValueError("Erro: A chave da API do DeepSeek não está configurada corretamente.")

if not DISCORD_TOKEN:
    raise ValueError("Erro: O token do Discord não está configurado corretamente.")

# Configuração do bot com AutoShardedBot para melhor desempenho
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.AutoShardedBot(command_prefix="!", intents=intents)

# Loop para pingar o Cloud Run e manter a instância ativa
async def keep_alive():
    while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://SEU_URL_DO_CLOUDRUN/health") as resp:
                    print("Pingando servidor, status:", resp.status)
            except Exception as e:
                print("Erro ao pingar Cloud Run:", e)
        await asyncio.sleep(300)  # A cada 5 minutos

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    bot.loop.create_task(keep_alive())  # Inicia o loop keep-alive
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": "🚀 O bot está online e funcionando!"})

@bot.command(aliases=["p"])
async def perguntar(ctx, *, pergunta: str):
    resposta = perguntar_ao_deepseek(pergunta)
    await ctx.send(f"**Pergunta:** {pergunta}\n**Resposta:** {resposta}")
    
    tts = gTTS(text=resposta, lang='pt-br', slow=False)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    
    await tocar_audio(ctx, audio_buffer)

if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)).start()
    try:
        bot.run(DISCORD_TOKEN)
    except discord.errors.LoginFailure:
        print("Erro: Token do Discord inválido. Verifique a configuração.")
