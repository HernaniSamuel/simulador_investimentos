# Use uma imagem Python como base
FROM python:3.10-slim

# Configure o diretório de trabalho no contêiner
WORKDIR /app

# Copie os arquivos necessários para o contêiner
COPY requirements.txt requirements.txt

# Instale as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Copie todo o código do projeto para o contêiner
COPY . .

# Copiar o arquivo .env para o diretório correto no contêiner
COPY simuladorinvestimentos/.env /app/simuladorinvestimentos/.env

# Configure o diretório de trabalho para o projeto
WORKDIR /app/simuladorinvestimentos

# Certifique-se de que o diretório de arquivos estáticos exista
RUN mkdir -p /app/staticfiles

# Coletar os arquivos estáticos
RUN python manage.py collectstatic --noinput

# Exponha a porta onde o Gunicorn irá rodar
EXPOSE 8000

# Comando padrão para rodar o Gunicorn
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
