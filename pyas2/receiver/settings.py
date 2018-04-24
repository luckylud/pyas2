"""
Django settings for pyas2 receiver.

"""

ROOT_URLCONF = 'pyas2.receiver.urls'

# WSGI_APPLICATION = 'pyas2.receiver.wsgi.application'

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'pyas2'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# PYAS2 receiver settings
from pyas2.pyas2init import Pyas2settingsModname
pyas2settings = __import__(Pyas2settingsModname())

from pyas2settings import PYAS2, DATABASES, MEDIA_ROOT, SECRET_KEY
from pyas2settings import AS2_ALLOWED_HOSTS as AS2_ALLOWED_HOSTS
if hasattr(pyas2settings, 'DEBUG'):
    from pyas2settings import DEBUG
if hasattr(pyas2settings, 'DATABASE_ROUTERS'):
    from pyas2settings import DATABASE_ROUTERS

PYAS2['SERVER'] = 'receiver'

ALLOWED_HOSTS = AS2_ALLOWED_HOSTS
