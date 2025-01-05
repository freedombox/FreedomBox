# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Setup Django web framework.
"""

import logging
import os
import pathlib
import random
import stat

import django.conf
import django.core.management
import django.core.wsgi
from django.conf import global_settings
from django.contrib.messages import constants as message_constants

from . import cfg, glib, log, module_loader, settings

logger = logging.getLogger(__name__)


def init():
    """Setup Django configuration in the absence of .settings file"""
    # Workaround for django-simple-captcha 0.5.6 not being compatible with
    # Django 3.2. 0.5.14 is almost there in Debian. Workaround only until then.
    django.utils.encoding.python_2_unicode_compatible = lambda x: x

    if cfg.secure_proxy_ssl_header:
        settings.SECURE_PROXY_SSL_HEADER = (cfg.secure_proxy_ssl_header,
                                            'https')

    if cfg.use_x_forwarded_for:
        settings.IPWARE_META_PRECEDENCE_ORDER = ('HTTP_X_FORWARDED_FOR', )

    settings.DATABASES['default']['NAME'] = cfg.store_file
    settings.DEBUG = cfg.develop
    settings.FORCE_SCRIPT_NAME = cfg.server_dir
    settings.INSTALLED_APPS += module_loader.get_modules_to_load()
    settings.LANGUAGES = get_languages()
    settings.LOGGING = log.get_configuration()
    settings.MESSAGE_TAGS = {message_constants.ERROR: 'danger'}
    settings.SECRET_KEY = _get_secret_key()
    settings.SESSION_FILE_PATH = os.path.join(cfg.data_dir, 'sessions')
    settings.STATIC_URL = '/'.join([cfg.server_dir,
                                    'static/']).replace('//', '/')
    settings.USE_X_FORWARDED_HOST = cfg.use_x_forwarded_host
    if cfg.develop:
        # Disable template caching in development so that page updates don't
        # require service restart.
        del settings.TEMPLATES[0]['APP_DIRS']
        settings.TEMPLATES[0]['OPTIONS']['loaders'] = [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]

    kwargs = {}
    for setting in dir(settings):
        if setting.isupper():
            kwargs[setting] = getattr(settings, setting)

    django.conf.settings.configure(**kwargs)
    django.setup(set_prefix=True)

    logger.debug('Configured Django with applications - %s',
                 ', '.join(settings.INSTALLED_APPS))


def post_init():
    """Perform operations after completing init of other modules."""
    logger.debug('Creating or adding new tables to data file')
    django.core.management.call_command('migrate', '--fake-initial',
                                        interactive=False, verbosity=0)
    os.chmod(cfg.store_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)

    # Cleanup expired sessions every day
    glib.schedule(24 * 3600, _cleanup_expired_sessions, in_thread=True)


def _get_secret_key():
    """Retrieve or create a new Django secret key."""
    secret_key_file = pathlib.Path(cfg.data_dir) / 'django-secret.key'
    if secret_key_file.exists():
        secret_key = secret_key_file.read_text()
        if len(secret_key) >= 128:
            return secret_key

    secret_key = _generate_secret_key()
    # File should be created with permission 0o700
    old_umask = os.umask(0o077)
    try:
        secret_key_file.write_text(secret_key)
    finally:
        os.umask(old_umask)

    return secret_key


def _generate_secret_key():
    """Generate a new random secret key for use with Django."""
    # We could have used django.core.management.utils.get_random_secret_key
    # but it is not documented and should be considered private.
    length = 128
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    rand = random.SystemRandom()
    return ''.join(rand.choice(chars) for _ in range(length))


def get_languages():
    """Return list of languages to show in the interface.

    Add additional languages that FreedomBox support but Django doesn't.

    """

    def gettext_noop(string):
        """Django's actual translation methods need Django to be setup."""
        return string

    return sorted(
        list(global_settings.LANGUAGES) + [
            ('gu', gettext_noop('Gujarati')),
        ])


def _cleanup_expired_sessions(data):
    """Cleanup expired Django sessions."""
    verbosity = 1 if cfg.develop else 0
    django.core.management.call_command('clearsessions', verbosity=verbosity)


def get_wsgi_application():
    """Return Django wsgi application."""
    return django.core.wsgi.get_wsgi_application()


def get_static_url():
    """Return Django static URL."""
    return django.conf.settings.STATIC_URL
