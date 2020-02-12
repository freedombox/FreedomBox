# SPDX-License-Identifier: AGPL-3.0-or-later
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

from . import cfg, log, module_loader, settings

logger = logging.getLogger(__name__)


def init():
    """Setup Django configuration in the absence of .settings file"""
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
    settings.SESSION_FILE_PATH = os.path.join(cfg.data_dir, 'sessions')
    settings.STATIC_URL = '/'.join([cfg.server_dir,
                                    'static/']).replace('//', '/')
    settings.USE_X_FORWARDED_HOST = cfg.use_x_forwarded_host

    kwargs = {}
    for setting in dir(settings):
        if setting.isupper():
            kwargs[setting] = getattr(settings, setting)

    django.conf.settings.configure(**kwargs)
    django.setup(set_prefix=True)

    logger.debug('Configured Django with applications - %s',
                 settings.INSTALLED_APPS)

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

    return sorted(
        list(global_settings.LANGUAGES) + [
            ('gu', gettext_noop('Gujarati')),
        ])


def get_wsgi_application():
    """Return Django wsgi application."""
    return django.core.wsgi.get_wsgi_application()


def get_static_url():
    """Return Django static URL."""
    return django.conf.settings.STATIC_URL


def get_ip_address_from_request(request):
    """Return the IP address of the original client."""
    if cfg.use_x_forwarded_for:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    return ip_address
