import os
import discord
from discord.ext import commands
from gtts import gTTS
from io import BytesIO
import asyncio
import requests
import shutil

# Configurações iniciais
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DEEPSEEK_API_KEY or not DISCORD_TOKEN:
    raise ValueError("Erro: A chave da API do DeepSeek ou o token do Discord não estão configurados corretamente.")

# Impede múltiplas instâncias do bot
if os.getenv("RUNNING_INSTANCE"):
    print("Uma instância do bot já está rodando. Encerrando esta nova execução...")
    exit()
os.environ["RUNNING_INSTANCE"] = "1"

# Configuração do bot do Discord
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lista para armazenar o histórico da conversa
messages = [{"role": "system", "content": "Você é uma IA ajudante em um RPG de cyberpunk de uma garota chamada Elizabeth..."}]

# Função para conversar com o DeepSeek
def perguntar_ao_deepseek(pergunta):
    global messages
    messages.append({"role": "user", "content": pergunta})

    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": messages}

    try:
        response = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        resposta_ia = response.json()["choices"][0]["message"]["content"]
        messages.append({"role": "assistant", "content": resposta_ia})
        return resposta_ia
    except Exception as e:
        print(f"Erro: {e}")
        return "Droga, parece que o sistema tomou um choque de alta voltagem. Tenta de novo!"

# Função para tocar o áudio no canal de voz
async def tocar_audio(ctx, audio_buffer):
    if ctx.author.voice and ctx.author.voice.channel:
        canal = ctx.author.voice.channel
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if not voice_client or not voice_client.is_connected():
            voice_client = await canal.connect(timeout=15)

        if voice_client.is_playing():
            voice_client.stop()

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            await ctx.send("Erro: ffmpeg não encontrado. O áudio não pode ser reproduzido.")
            return

        ffmpeg_options = "-filter:a atempo=1.50,asetrate=44100*0.69"
        source = discord.FFmpegPCMAudio(audio_buffer, executable=ffmpeg_path, options=ffmpeg_options)
        voice_client.play(source)

        while voice_client.is_playing():
            await asyncio.sleep(1)

        await voice_client.disconnect()
    else:
        await ctx.send("Você precisa estar em um canal de voz para eu falar!")

# Evento de inicialização
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": "🚀 O bot está online e funcionando!"})

# Comando para perguntar ao DeepSeek
@bot.command(aliases=["p"])
async def perguntar(ctx, *, pergunta: str):
    resposta = perguntar_ao_deepseek(pergunta)
    await ctx.send(f"**Pergunta:** {pergunta}\n**Resposta:** {resposta}")

    tts = gTTS(text=resposta, lang='pt-br', slow=False)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    await tocar_audio(ctx, audio_buffer)

# Rodando o bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
