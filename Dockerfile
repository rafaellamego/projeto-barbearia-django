FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências de sistema necessárias para compilar/rodar pacotes
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Coleta os arquivos estáticos do front-end
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Roda o servidor Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "barbearia.wsgi:application"]