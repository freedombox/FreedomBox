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
Setup Django web framework.
"""

import logging
import os
import stat

import django.conf
import django.core.management
import django.core.wsgi
from django.conf import global_settings
from django.contrib.messages import constants as message_constants

from . import cfg, log, module_loader

logger = logging.getLogger(__name__)


def init():
    """Setup Django configuration in the absence of .settings file"""
    templates = [
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

    applications = [
        'axes',
        'captcha',
        'bootstrapform',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.messages',
        'stronghold',
        'plinth',
    ]
    applications += module_loader.get_modules_to_load()
    sessions_directory = os.path.join(cfg.data_dir, 'sessions')

    secure_proxy_ssl_header = None
    if cfg.secure_proxy_ssl_header:
        secure_proxy_ssl_header = (cfg.secure_proxy_ssl_header, 'https')

    pwd = 'django.contrib.auth.password_validation'

    django.conf.settings.configure(
        ALLOWED_HOSTS=['*'],
        AUTH_PASSWORD_VALIDATORS=[
            {
                'NAME': '{}.UserAttributeSimilarityValidator'.format(pwd),
            },
            {
                'NAME': '{}.MinimumLengthValidator'.format(pwd),
                'OPTIONS': {
                    'min_length': 8,
                }
            },
            {
                'NAME': '{}.CommonPasswordValidator'.format(pwd),
            },
            {
                'NAME': '{}.NumericPasswordValidator'.format(pwd),
            },
        ],
        AXES_LOCKOUT_URL='locked/',
        AXES_BEHIND_REVERSE_PROXY=True,
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
            }
        },
        CAPTCHA_FONT_PATH=[
            '/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf'
        ],
        CAPTCHA_LENGTH=6,
        CAPTCHA_FLITE_PATH='/usr/bin/flite',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': cfg.store_file
            }
        },
        DEBUG=cfg.develop,
        FORCE_SCRIPT_NAME=cfg.server_dir,
        INSTALLED_APPS=applications,
        IPWARE_META_PRECEDENCE_ORDER=('HTTP_X_FORWARDED_FOR', ),
        LANGUAGES=get_languages(),
        LOGGING=log.get_configuration(),
        LOGIN_URL='users:login',
        LOGIN_REDIRECT_URL='index',
        MESSAGE_TAGS={message_constants.ERROR: 'danger'},
        MIDDLEWARE=(
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'stronghold.middleware.LoginRequiredMiddleware',
            'plinth.middleware.AdminRequiredMiddleware',
            'plinth.middleware.FirstSetupMiddleware',
            'plinth.modules.first_boot.middleware.FirstBootMiddleware',
            'plinth.middleware.SetupMiddleware',
        ),
        PASSWORD_HASHERS=[
            'django.contrib.auth.hashers.Argon2PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
            'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
        ],
        ROOT_URLCONF='plinth.urls',
        SECURE_BROWSER_XSS_FILTER=True,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        SECURE_PROXY_SSL_HEADER=secure_proxy_ssl_header,
        SESSION_ENGINE='django.contrib.sessions.backends.file',
        SESSION_FILE_PATH=sessions_directory,
        STATIC_URL='/'.join([cfg.server_dir, 'static/']).replace('//', '/'),
        # STRONGHOLD_PUBLIC_URLS=(r'^captcha/', ),
        STRONGHOLD_PUBLIC_NAMED_URLS=(
            'captcha-image',
            'captcha-image-2x',
            'captcha-audio',
            'captcha-refresh',
        ),
        TEMPLATES=templates,
        USE_L10N=True,
        USE_X_FORWARDED_HOST=cfg.use_x_forwarded_host)
    django.setup(set_prefix=True)

    logger.debug('Configured Django with applications - %s', applications)

    logger.debug('Creating or adding new tables to data file')
    verbosity = 1 if cfg.develop else 0
    django.core.management.call_command('migrate', '--fake-initial',
                                        interactive=False, verbosity=verbosity)
    os.chmod(cfg.store_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)


def get_languages():
    """Return list of languages to show in the interface.

    Add additional languages that FreedomBox support but Django doesn't.

    """
    def gettext_noop(string):
        """Django's actual translation methods need Django to be setup."""
        return string

    return sorted(list(global_settings.LANGUAGES) + [
        ('gu', gettext_noop('Gujarati')),
    ])


def get_wsgi_application():
    """Return Django wsgi application."""
    return django.core.wsgi.get_wsgi_application()


def get_static_url():
    """Return Django static URL."""
    return django.conf.settings.STATIC_URL
