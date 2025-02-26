# Usa uma imagem base com Python
FROM python:3.10

# Instala ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . /app

# Instala as dependências
RUN pip install -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]

EXPOSE 8080
