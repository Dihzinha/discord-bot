import os
import discord
from discord.ext import commands
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
import asyncio
from flask import Flask, request
from flask_cors import CORS
import threading
import requests

# Configurações iniciais
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/beta"
)

# Configurações do bot do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lista para armazenar o histórico da conversa
messages = [
    {"role": "system", "content": "Você é uma IA ajudante em um RPG de cyberpunk de uma garota chamada Elizabeth , e não é so ela que fala com você, outras pessoas tambem podem se comunicar com você. Fale de forma sarcástica e acelerada, em alguns momentos fazendo referências ao mundo cyberpunk. Seja exagerado e dramático às vezes. Evite usar emojis. Evite mencionar que esta em um mundo cyberpunk e tente agir como se realmente vivesse naquele mundo. Evite mensagens muito longas e virgulas. Começe sempre suas respostas com um 'bip-bop'"}
]

def perguntar_ao_deepseek(pergunta):
    global messages
    messages.append({"role": "user", "content": pergunta})

    try:
        resposta = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=100
        )
        resposta_ia = resposta.choices[0].message.content
        messages.append({"role": "assistant", "content": resposta_ia})
        return resposta_ia
    except Exception as e:
        print(f"Erro: {e}")
        return "Droga, parece que o sistema tomou um choque de alta voltagem. Tenta de novo!"

async def tocar_audio(ctx, audio_buffer):
    if ctx.author.voice and ctx.author.voice.channel:
        canal = ctx.author.voice.channel

        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice_client:
            voice_client = await canal.connect()
            await asyncio.sleep(1)

        temp_audio_file = "resposta.mp3"
        with open(temp_audio_file, "wb") as f:
            f.write(audio_buffer.getvalue())

        print(f"Áudio gerado: {temp_audio_file}")

        await asyncio.sleep(0.5)  # Redução ainda maior do atraso para tocar mais rápido

        ffmpeg_options = "-filter:a atempo=1.50,asetrate=44100*0.69"  # Voz mais rápida e robótica
        source = discord.FFmpegPCMAudio(temp_audio_file, options=ffmpeg_options)

        print(f"Tentando tocar áudio em: {temp_audio_file}")
        voice_client.play(source)

        while voice_client.is_playing():
            await asyncio.sleep(1)

        await voice_client.disconnect()
        os.remove(temp_audio_file)
    else:
        await ctx.send("Você precisa estar em um canal de voz para eu falar! Onde mais eu poderia transmitir minha gloriosa sabedoria robótica?")

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
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

# Servidor Flask para manter o bot online
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET', 'HEAD'])
def home():
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": "🔍 O UptimeRobot verificou o bot e ele está ativo."})
    return "Bot online!", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_TOKEN)