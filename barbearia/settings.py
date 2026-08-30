import os
from pathlib import Path
import pymysql

# Configuração para usar PyMySQL como backend do MySQL
pymysql.version_info = (2, 2, 8, "final", 0)
pymysql.install_as_MySQLdb()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# SECURITY WARNING: use variáveis de ambiente ou defina uma chave segura em produção
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-!*h-cagz$jbrn1^-==wxo5ij366=0ika7s%s4uhtx2slb$enff')

# Em produção com Docker, o DEBUG deve ser False por padrão (ou lido da env)
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# Liberar acessos (o '*' aceita o IP da Oracle ou seu domínio)
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '147.15.102.248').split(',')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.DjangoTemplates',
        # Adicione o caminho da sua pasta de templates aqui:
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'agenda',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # <-- 1. ADICIONADO PARA O FRONTEND/CSS FUNCIONAR NO DOCKER
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'barbearia.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'barbearia.wsgi.application'


# Database (ALTERADO DE SQLITE PARA MYSQL)
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'barbearia_db'),
        'USER': os.getenv('MYSQL_USER', 'barbearia_user'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', 'senha_banco_segura'),
        'HOST': os.getenv('DB_HOST', 'db'),  # 'db' é o nome do container do MySQL no docker-compose
        'PORT': os.getenv('MYSQL_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# Traduzido para PT-BR e horário do Brasil
LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# CONFIGURAÇÃO DE PRODUÇÃO PARA OS ARQUIVOS ESTÁTICOS DO FRONTEND
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'