"""
Django settings for LinuxGuard project.
LinuxGuard – Intelligent Linux Server Monitoring & Auto-Remediation Platform
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-linuxguard-super-secret-key-change-in-production-2026!'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,*').split(',')
    if host.strip()
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # LinuxGuard Core Application
    'monitoring.apps.MonitoringConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'linuxguard.urls'

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
                'monitoring.context_processors.global_navigation_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'linuxguard.wsgi.application'
ASGI_APPLICATION = 'linuxguard.asgi.application'

# Database configuration
DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite3').lower()

if DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'linuxguard'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.environ.get('DB_NAME', 'db.sqlite3'),
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'monitoring.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LinuxGuard Default Thresholds
LINUXGUARD_CONFIG = {
    'CPU_WARN': float(os.environ.get('CPU_WARNING_THRESHOLD', 85.0)),
    'CPU_CRIT': float(os.environ.get('CPU_CRITICAL_THRESHOLD', 95.0)),
    'RAM_WARN': float(os.environ.get('RAM_WARNING_THRESHOLD', 85.0)),
    'RAM_CRIT': float(os.environ.get('RAM_CRITICAL_THRESHOLD', 95.0)),
    'DISK_WARN': float(os.environ.get('DISK_WARNING_THRESHOLD', 80.0)),
    'DISK_CRIT': float(os.environ.get('DISK_CRITICAL_THRESHOLD', 90.0)),
    'SSH_FAIL_LIMIT': int(os.environ.get('SSH_FAILURE_LIMIT', 5)),
    'SSH_WINDOW_MINUTES': int(os.environ.get('SSH_WINDOW_MINUTES', 10)),
    'AUTO_REMEDIATE_SAFE_SERVICES': os.environ.get('AUTO_REMEDIATE_SAFE_SERVICES', 'True').lower() in ('true', '1', 't'),
}
