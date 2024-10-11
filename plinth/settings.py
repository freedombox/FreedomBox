#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Basic settings for Django web framework.

During initialization of the service, these settings are overridden before
Django is initialized. However, this file has been written in this format to
let Django initialization easier in other situations such as test cases,
documentation generation, debugging etc.

See: https://docs.djangoproject.com/en/dev/ref/settings/

"""

import django

ALLOWED_HOSTS = ['*']

_pwd = 'django.contrib.auth.password_validation'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': '{}.UserAttributeSimilarityValidator'.format(_pwd),
    },
    {
        'NAME': '{}.MinimumLengthValidator'.format(_pwd),
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': '{}.CommonPasswordValidator'.format(_pwd),
    },
    {
        'NAME': '{}.NumericPasswordValidator'.format(_pwd),
    },
]

AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend should be the first backend. If the user is locked
    # out due to too many attempts, the backend denies further attempts untill
    # unlocked by a CAPTCHA form.
    'axes.backends.AxesStandaloneBackend',

    # Django ModelBackend is the default authentication backend.
    'django.contrib.auth.backends.ModelBackend',
]

AXES_LOCKOUT_URL = 'locked/'

AXES_RESET_ON_SUCCESS = True

AXES_VERBOSE = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

CAPTCHA_FONT_PATH = ['/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf']

CAPTCHA_LENGTH = 6

CAPTCHA_FLITE_PATH = '/usr/bin/flite'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'OPTIONS': {
            'timeout': 30
        },
        # Overridden based on the configuration key store_file
        'NAME': '/var/lib/plinth/plinth.sqlite3'
    }
}

# Overridden based on command line argument --develop
DEBUG = False

# This is already the default (Django 3.2), however, setting it explicitly
# seems to avoid a warning while running 'django-admin makemigrations'.
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# /tmp, the default value for this setting, is mounted as tmpfs which is in
# RAM. It can only handle files of size proportionate to the amount of
# available RAM. /var/tmp is on a physical disk. Most of the time, /var/tmp
# will on the same file system as the final destination of the uploaded file,
# which is the app's storage folder in /var/lib/. This eliminates an extra disk
# copy operation. Left over files in /var/tmp/ will be cleaned up when service
# stops due to PrivateTmp=yes in service's systemd unit.
FILE_UPLOAD_TEMP_DIR = '/var/tmp'

# Disable MemoryFileUploadHandler to handle files of all sizes in the same way.
# Uploaded files need to be handled by privileged methods (in a separate
# process) in order to move to the target service's directory and set required
# ownership and permissions.
FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
]

# Overridden based on the configuration key server_dir
FORCE_SCRIPT_NAME = '/plinth'

# FreedomBox apps are appended to this list
INSTALLED_APPS = [
    'axes',
    'captcha',
    'bootstrapform',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'stronghold',
    'plinth',
]

# Overridden based on configuration key use_x_forwarded_host
IPWARE_META_PRECEDENCE_ORDER = ('REMOTE_ADDR', )

# Overridden by get_languages()
LANGUAGES = [('en', 'English')]

# Overridden by log configuration in log.py
LOGGING = {'version': 1}

LOGIN_URL = 'users:login'

LOGIN_REDIRECT_URL = 'index'

# Overridden before initialization
MESSAGE_TAGS: dict = {}

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'plinth.middleware.CommonErrorMiddleware',
    'stronghold.middleware.LoginRequiredMiddleware',
    'plinth.middleware.AdminRequiredMiddleware',
    'plinth.middleware.FirstSetupMiddleware',
    'plinth.modules.first_boot.middleware.FirstBootMiddleware',
    'plinth.middleware.SetupMiddleware',

    # AxesMiddleware should be the last middleware. It only formats user
    # lockout messages and renders Axes lockout responses on failed user
    # authentication attempts from login views.
    'axes.middleware.AxesMiddleware',
)

PASSWORD_HASHERS = [
    'plinth.hashers.Argon2PasswordHasherLowMemory',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

ROOT_URLCONF = 'plinth.urls'

SECURE_CONTENT_TYPE_NOSNIFF = True

# Overridden based configuration key secure_proxy_ssl_header
SECURE_PROXY_SSL_HEADER = None

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

SESSION_FILE_PATH = '/var/lib/plinth/sessions'

# Overridden based on configuration key server_dir
STATIC_URL = '/plinth/static/'

# STRONGHOLD_PUBLIC_URLS=(r'^captcha/', )

STRONGHOLD_PUBLIC_NAMED_URLS = (
    'captcha-image',
    'captcha-image-2x',
    'captcha-audio',
    'captcha-refresh',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'plinth.context_processors.common',
            ],
        },
    },
]

TIME_ZONE = 'UTC'

if django.VERSION <= (4, 0):
    USE_L10N = True

USE_TZ = True

# Overridden by configuration setting use_x_forwarded_host
USE_X_FORWARDED_HOST = False
