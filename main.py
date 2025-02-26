import os
import discord
from discord.ext import commands
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
import asyncio
import requests
from flask import Flask

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

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Configuração do bot do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lista para armazenar o histórico da conversa
messages = [
    {"role": "system", "content": "Você é uma IA ajudante em um RPG de cyberpunk de uma garota chamada Elizabeth , e não é so ela que fala com você, outras pessoas tambem podem se comunicar com você. Fale de forma sarcástica e acelerada, em alguns momentos fazendo referências ao mundo cyberpunk. Seja exagerado e dramático às vezes. Evite usar emojis. Evite mencionar que esta em um mundo cyberpunk e tente agir como se realmente vivesse naquele mundo. Evite mensagens longas e virgulas. Começe sempre suas respostas com um 'bip-bop', de respostas pequenas"}
]

def perguntar_ao_deepseek(pergunta):
    global messages
    messages.append({"role": "user", "content": pergunta})

    try:
        resposta = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
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

        ffmpeg_options = "-filter:a atempo=1.50,asetrate=44100*0.69"  # Voz mais rápida e robótica
        source = discord.FFmpegPCMAudio(temp_audio_file, options=ffmpeg_options)

        voice_client.play(source)

        while voice_client.is_playing():
            await asyncio.sleep(1)

        await voice_client.disconnect()
        os.remove(temp_audio_file)
    else:
        await ctx.send("Você precisa estar em um canal de voz para eu falar!")

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

if __name__ == "__main__":
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)).start()
    bot.run(DISCORD_TOKEN)
