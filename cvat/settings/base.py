# Copyright (C) 2018-2019 Intel Corporation
#
# SPDX-License-Identifier: MIT

"""
Django settings for CVAT project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import sys
import fcntl
import shutil
import subprocess
import mimetypes
mimetypes.add_type("application/wasm", ".wasm", True)

from pathlib import Path

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = str(Path(__file__).parents[2])

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
INTERNAL_IPS = ['127.0.0.1']

try:
    sys.path.append(BASE_DIR)
    from keys.secret_key import SECRET_KEY # pylint: disable=unused-import
except ImportError:

    from django.utils.crypto import get_random_string
    keys_dir = os.path.join(BASE_DIR, 'keys')
    if not os.path.isdir(keys_dir):
        os.mkdir(keys_dir)
    with open(os.path.join(keys_dir, 'secret_key.py'), 'w') as f:
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        f.write("SECRET_KEY = '{}'\n".format(get_random_string(50, chars)))
    from keys.secret_key import SECRET_KEY


def generate_ssh_keys():
    keys_dir = '{}/keys'.format(os.getcwd())
    ssh_dir = '{}/.ssh'.format(os.getenv('HOME'))
    pidfile = os.path.join(ssh_dir, 'ssh.pid')

    with open(pidfile, "w") as pid:
        fcntl.flock(pid, fcntl.LOCK_EX)
        try:
            subprocess.run(['ssh-add {}/*'.format(ssh_dir)], shell = True, stderr = subprocess.PIPE)
            keys = subprocess.run(['ssh-add -l'], shell = True,
                stdout = subprocess.PIPE).stdout.decode('utf-8').split('\n')
            if 'has no identities' in keys[0]:
                print('SSH keys were not found')
                volume_keys = os.listdir(keys_dir)
                if not ('id_rsa' in volume_keys and 'id_rsa.pub' in volume_keys):
                    print('New pair of keys are being generated')
                    subprocess.run(['ssh-keygen -b 4096 -t rsa -f {}/id_rsa -q -N ""'.format(ssh_dir)], shell = True)
                    shutil.copyfile('{}/id_rsa'.format(ssh_dir), '{}/id_rsa'.format(keys_dir))
                    shutil.copymode('{}/id_rsa'.format(ssh_dir), '{}/id_rsa'.format(keys_dir))
                    shutil.copyfile('{}/id_rsa.pub'.format(ssh_dir), '{}/id_rsa.pub'.format(keys_dir))
                    shutil.copymode('{}/id_rsa.pub'.format(ssh_dir), '{}/id_rsa.pub'.format(keys_dir))
                else:
                    print('Copying them from keys volume')
                    shutil.copyfile('{}/id_rsa'.format(keys_dir), '{}/id_rsa'.format(ssh_dir))
                    shutil.copymode('{}/id_rsa'.format(keys_dir), '{}/id_rsa'.format(ssh_dir))
                    shutil.copyfile('{}/id_rsa.pub'.format(keys_dir), '{}/id_rsa.pub'.format(ssh_dir))
                    shutil.copymode('{}/id_rsa.pub'.format(keys_dir), '{}/id_rsa.pub'.format(ssh_dir))
                subprocess.run(['ssh-add', '{}/id_rsa'.format(ssh_dir)], shell = True)
        finally:
            fcntl.flock(pid, fcntl.LOCK_UN)

try:
    if os.getenv("SSH_AUTH_SOCK", None):
        generate_ssh_keys()
except Exception:
    pass

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cvat.apps.authentication',
    'cvat.apps.documentation',
    'cvat.apps.dataset_manager',
    'cvat.apps.engine',
    'cvat.apps.git',
    'cvat.apps.restrictions',
    'cvat.apps.lambda_manager',
    'django_rq',
    'compressor',
    'cacheops',
    'sendfile',
    'dj_pagination',
    'revproxy',
    'rules',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_yasg',
    'rest_auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'corsheaders',
    'allauth.socialaccount',
    'rest_auth.registration'
]

SITE_ID = 1

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'cvat.apps.authentication.auth.TokenAuthentication',
        'cvat.apps.authentication.auth.SignatureAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_VERSIONING_CLASS':
        # Don't try to use URLPathVersioning. It will give you /api/{version}
        # in path and '/api/docs' will not collapse similar items (flat list
        # of all possible methods isn't readable).
        'rest_framework.versioning.NamespaceVersioning',
    # Need to add 'api-docs' here as a workaround for include_docs_urls.
    'ALLOWED_VERSIONS': ('v1', 'api-docs'),
    'DEFAULT_PAGINATION_CLASS':
        'cvat.apps.engine.pagination.CustomPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter'),

    # Disable default handling of the 'format' query parameter by REST framework
    'URL_FORMAT_OVERRIDE': 'scheme',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
    },
}

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'cvat.apps.restrictions.serializers.RestrictedRegisterSerializer'
}

if os.getenv('DJANGO_LOG_VIEWER_HOST'):
    INSTALLED_APPS += ['cvat.apps.log_viewer']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    # FIXME
    # 'corsheaders.middleware.CorsPostCsrfMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dj_pagination.middleware.PaginationMiddleware',
]

UI_URL = ''

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

ROOT_URLCONF = 'cvat.urls'

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

WSGI_APPLICATION = 'cvat.wsgi.application'

# Django Auth
DJANGO_AUTH_TYPE = 'BASIC'
DJANGO_AUTH_DEFAULT_GROUPS = []
LOGIN_URL = 'rest_login'
LOGIN_REDIRECT_URL = '/'
AUTH_LOGIN_NOTE = '<p>Have not registered yet? <a href="/auth/register">Register here</a>.</p>'

AUTHENTICATION_BACKENDS = [
    'rules.permissions.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend'
]

# https://github.com/pennersr/django-allauth
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Django-RQ
# https://github.com/rq/django-rq

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': '4h'
    },
    'low': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'DEFAULT_TIMEOUT': '24h'
    }
}

NUCLIO = {
    'SCHEME': 'http',
    'HOST': 'localhost',
    'PORT': 8070,
    'DEFAULT_TIMEOUT': 120
}

RQ_SHOW_ADMIN_LINK = True
RQ_EXCEPTION_HANDLERS = ['cvat.apps.engine.views.rq_handler']


# JavaScript and CSS compression
# https://django-compressor.readthedocs.io

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter'
]
COMPRESS_JS_FILTERS = []  # No compression for js files (template literals were compressed bad)

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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

# Cache DB access (e.g. for engine.task.get_frame)
# https://github.com/Suor/django-cacheops
CACHEOPS_REDIS = {
    'host': 'localhost', # redis-server is on same machine
    'port': 6379,        # default redis port
    'db': 1,             # SELECT non-default redis database
}

CACHEOPS = {
    # Automatically cache any Task.objects.get() calls for 15 minutes
    # This also includes .first() and .last() calls.
    'engine.task': {'ops': 'get', 'timeout': 60*15},

    # Automatically cache any Job.objects.get() calls for 15 minutes
    # This also includes .first() and .last() calls.
    'engine.job': {'ops': 'get', 'timeout': 60*15},
}

CACHEOPS_DEGRADE_ON_FAILURE = True

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.getenv('TZ', 'Etc/UTC')

USE_I18N = True

USE_L10N = True

USE_TZ = True

CSRF_COOKIE_NAME = "csrftoken"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
os.makedirs(STATIC_ROOT, exist_ok=True)

DATA_ROOT = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_ROOT, exist_ok=True)

MEDIA_DATA_ROOT = os.path.join(DATA_ROOT, 'data')
os.makedirs(MEDIA_DATA_ROOT, exist_ok=True)

TASKS_ROOT = os.path.join(DATA_ROOT, 'tasks')
os.makedirs(TASKS_ROOT, exist_ok=True)

SHARE_ROOT = os.path.join(BASE_DIR, 'share')
os.makedirs(SHARE_ROOT, exist_ok=True)

MODELS_ROOT = os.path.join(DATA_ROOT, 'models')
os.makedirs(MODELS_ROOT, exist_ok=True)

LOGS_ROOT = os.path.join(BASE_DIR, 'logs')
os.makedirs(MODELS_ROOT, exist_ok=True)

MIGRATIONS_LOGS_ROOT = os.path.join(LOGS_ROOT, 'migrations')
os.makedirs(MIGRATIONS_LOGS_ROOT, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': [],
            'formatter': 'standard',
        },
        'server_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'filename': os.path.join(BASE_DIR, 'logs', 'cvat_server.log'),
            'formatter': 'standard',
            'maxBytes': 1024*1024*50, # 50 MB
            'backupCount': 5,
        },
        'logstash': {
            'level': 'INFO',
            'class': 'logstash.TCPLogstashHandler',
            'host': os.getenv('DJANGO_LOG_SERVER_HOST', 'localhost'),
            'port': os.getenv('DJANGO_LOG_SERVER_PORT', 5000),
            'version': 1,
            'message_type': 'django',
        }
    },
    'loggers': {
        'cvat.server': {
            'handlers': ['console', 'server_file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },

        'cvat.client': {
            'handlers': [],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },

        'revproxy': {
            'handlers': ['console', 'server_file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG')
        },
        'django': {
            'handlers': ['console', 'server_file'],
            'level': 'INFO',
            'propagate': True
        }
    },
}

if os.getenv('DJANGO_LOG_SERVER_HOST'):
    LOGGING['loggers']['cvat.server']['handlers'] += ['logstash']
    LOGGING['loggers']['cvat.client']['handlers'] += ['logstash']

DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = None   # this django check disabled
LOCAL_LOAD_MAX_FILES_COUNT = 500
LOCAL_LOAD_MAX_FILES_SIZE = 512 * 1024 * 1024  # 512 MB

DATUMARO_PATH = os.path.join(BASE_DIR, 'datumaro')
sys.path.append(DATUMARO_PATH)

RESTRICTIONS = {
    'user_agreements': [],

    # this setting limits the number of tasks for the user
    'task_limit': None,

    # this setting reduse task visibility to owner and assignee only
    'reduce_task_visibility': True,

    # allow access to analytics component to users with the following roles
    'analytics_access': (
        'engine.role.observer',
        'engine.role.annotator',
        'engine.role.user',
        'engine.role.admin',
        ),
}
