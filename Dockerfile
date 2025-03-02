# Usa uma imagem oficial do Python como base
FROM python:3.10

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do bot para o container
COPY . /app

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Instala o ffmpeg para reprodução de audio
RUN apt-get update && apt-get install -y ffmpeg

# Define as variáveis de ambiente
ENV PYTHONUNBUFFERED=1

# Expõe a porta usada pelo Flask
EXPOSE 8080

# Comando para iniciar o bot
CMD ["python", "/app/main.py"]
