from pathlib import Path

# Базовая директория
BASE_DIR = Path(__file__).resolve().parent.parent

# Безопасность
SECRET_KEY = 'django-insecure-i)w-9rh2^6=ubbt0r5o8dwrbjrfen%dt!m0jw&^d3$1)w(9ir3'
DEBUG = True
ALLOWED_HOSTS = []
AUTH_USER_MODEL = 'marketplace.User'

# Установленные приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'marketplace',
    'django.contrib.humanize',

]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLs
ROOT_URLCONF = 'Krivoruchka.urls'

# Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'marketplace.views.base_context',
                'marketplace.context_processors.unread_notifications',
                'marketplace.context_processors.unread_chats',
            ],
        },
    },
]
CSP_SCRIPT_SRC = [
    "'self'",
    "'unsafe-inline'",  # Разрешаем inline-скрипты
    "'unsafe-eval'",    # Разрешаем eval (временно для работы setInterval)
]
WSGI_APPLICATION = 'Krivoruchka.wsgi.application'

# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Валидаторы паролей
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

# Язык и часовой пояс
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Статика
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Медиафайлы
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Переадресации
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Прочее
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
PROFILE_REQUIRED_FIELDS = ['phone', 'address']

import sys
if 'runserver' in sys.argv:
    from django.db import connection
    try:
        connection.ensure_connection()
        print("✓ База данных подключена успешно")
    except Exception as e:
        print(f"× Ошибка подключения к БД: {e}")
