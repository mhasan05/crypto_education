from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import timedelta
import dj_database_url

load_dotenv()  # take environment variables from .env.

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


AUTH_USER_MODEL = 'account.User'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'account',
    'settings',
    'tutorials',
    'notifications',
    'social_django',
    'ai',
    'feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'


# settings.py

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
}

SIMPLE_JWT = {
    'USER_ID_FIELD': 'user_id',
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


DATABASES = {
    'default': dj_database_url.parse(
        os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles', 'static')
MEDIA_URLS ='/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# SMTP_SETUP-----
EMAIL_USE_SSL = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'noreplay820@gmail.com'
EMAIL_HOST_PASSWORD = 'acjgoiavxgajkswn'
EMAIL_PORT = 465
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


AWS_ACCESS_KEY_ID = 'AKIAQNIVLQZ3FG2KJ3PE'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'my-bucket-crypto'
AWS_S3_SIGNATURE_NAME = 's3v4'
AWS_S3_REGION_NAME = 'eu-north-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL =  None
AWS_S3_VERIFY = True
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_SIGNATURE_NAME = os.getenv('AWS_S3_SIGNATURE_NAME')
# AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
# AWS_S3_FILE_OVERWRITE = os.getenv('AWS_S3_FILE_OVERWRITE')
# AWS_DEFAULT_ACL =  os.getenv('AWS_DEFAULT_ACL')
# AWS_S3_VERIFY = os.getenv('AWS_S3_VERIFY')
# DEFAULT_FILE_STORAGE = os.getenv('DEFAULT_FILE_STORAGE')


AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)


# settings.py

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_CLIENT_ID')  # or hardcode it
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')



CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://172.252.13.79:3000",
    "http://localhost:5173",
]




