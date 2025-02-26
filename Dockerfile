# Usa uma imagem base com Python
FROM python:3.10

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências
RUN pip install -r requirements.txt

# Comando para rodar o bot
CMD ["python", "main.py"]
