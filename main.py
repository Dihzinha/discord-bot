import os
import discord
from discord.ext import commands
from openai import OpenAI
from gtts import gTTS
from io import BytesIO
import asyncio
import requests

# Configurações iniciais
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
REPLIT_API_URL = os.getenv("REPLIT_API_URL")  # URL da API de Deployments do Replit
REPLIT_API_KEY = os.getenv("REPLIT_API_KEY")  # Chave da API do Replit

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/beta"
)

# Configuração do bot do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lista para armazenar o histórico da conversa
messages = [
    {"role": "system", "content": "Você é uma IA ajudante em um RPG de cyberpunk de uma garota chamada Elizabeth..."}
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
    # Ativar o Replit via API antes de responder
    if REPLIT_API_URL and REPLIT_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {REPLIT_API_KEY}"}
            response = requests.post(REPLIT_API_URL, headers=headers)
            if response.status_code == 200:
                await ctx.send("🚀 Ativando o Replit, aguarde...")
                await asyncio.sleep(10)  # Tempo para garantir que o Replit inicie
            else:
                await ctx.send("⚠️ Falha ao ativar o Replit!")
        except Exception as e:
            await ctx.send("⚠️ Erro ao tentar ativar o Replit!")
            print(e)
    
    resposta = perguntar_ao_deepseek(pergunta)
    await ctx.send(f"**Pergunta:** {pergunta}\n**Resposta:** {resposta}")

    tts = gTTS(text=resposta, lang='pt-br', slow=False)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    await tocar_audio(ctx, audio_buffer)

    # Manter o bot ativo por 10 minutos antes de desligar
    await asyncio.sleep(600)
    await ctx.send("⏳ Nenhuma interação detectada, desligando...")
    os._exit(0)  # Encerra o processo

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(DISCORD_TOKEN)
