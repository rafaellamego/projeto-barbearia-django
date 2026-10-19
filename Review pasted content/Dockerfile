FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# PyMySQL e puro Python: nao precisa de gcc nem libmysqlclient-dev.
# curl fica para o healthcheck / debug dentro do container.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# Sem "|| true": se o collectstatic falhar, o build precisa falhar aqui e
# nao em producao (o ManifestStaticFilesStorage quebra sem o manifesto).
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "barbearia.wsgi:application"]
