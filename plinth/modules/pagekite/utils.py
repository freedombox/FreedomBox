# SPDX-License-Identifier: AGPL-3.0-or-later
"""Utilities for configuring Pagekite."""

import logging
import os

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth.signals import domain_added, domain_removed

LOGGER = logging.getLogger(__name__)

# defaults for the credentials; @kitename acts as a placeholder and is
# understood (and replaced with the actual kitename) by pagekite.
BACKEND_HOST = 'localhost'
KITE_NAME = '@kitename'
KITE_SECRET = '@kitesecret'

# Augeas base path for Pagekite configuration files
CONF_PATH = '/files/etc/pagekite.d'

# Kite name used by default in config. Should be treated as unconfigured.
UNCONFIGURED_KITE = 'NAME.pagekite.me'

# Parameters that get stored in configuration service_on entries
SERVICE_PARAMS = [
    'protocol', 'kitename', 'backend_host', 'backend_port', 'secret'
]

# Predefined services are used to build the PredefinedServiceForm
#
# ATTENTION: When changing the params, make sure that the AddCustomServiceForm
# still recognizes when you try to add a service equal to a predefined one
PREDEFINED_SERVICES = {
    'http': {
        'params': {
            'protocol': 'http',
            'kitename': KITE_NAME,
            'backend_port': '80',
            'backend_host': BACKEND_HOST,
            'secret': KITE_SECRET
        },
        'label':
            _('Web Server (HTTP)'),
        'help_text':
            _('Site will be available at '
              '<a href=\"http://{0}\">http://{0}</a>'),
    },
    'https': {
        'params': {
            'protocol': 'https',
            'kitename': KITE_NAME,
            'backend_port': '443',
            'backend_host': BACKEND_HOST,
            'secret': KITE_SECRET
        },
        'label':
            _('Web Server (HTTPS)'),
        'help_text':
            _('Site will be available at '
              '<a href=\"https://{0}\">https://{0}</a>'),
    },
    'ssh': {
        'params': {
            'protocol': 'raw/22',
            'kitename': KITE_NAME,
            'backend_port': '22',
            'backend_host': BACKEND_HOST,
            'secret': KITE_SECRET
        },
        'label':
            _('Secure Shell (SSH)'),
        'help_text':
            _('See SSH client setup <a href="'
              'https://pagekite.net/wiki/Howto/SshOverPageKite/">'
              'instructions</a>')
    },
}


def convert_service_to_string(service):
    """ Convert service dict into a ":"-separated parameter string

    >>> convert_service_to_string({'kitename': '@kitename', \
'backend_host': 'localhost', 'secret': '@kitesecret', \
'protocol': 'https/443', 'backend_port': '443'})
    'https/443:@kitename:localhost:443:@kitesecret'
    """
    try:
        service_string = ":".join([service[param] for param in SERVICE_PARAMS])
    except KeyError:
        raise ValueError("Could not parse params: %s " % service)
    return service_string


def load_service(service):
    """Create a service out of json command-line argument.

    1) parse json
    2) only use the parameters that we need (SERVICE_PARAMS)
    3) convert unicode to strings
    """
    return {str(key): str(service[key]) for key in SERVICE_PARAMS}


def get_augeas_servicefile_path(protocol):
    """Get the augeas path where a service for a protocol should be stored

    TODO: Once we use python3 switch from doctests to unittests

    >>> get_augeas_servicefile_path('http')
    '/files/etc/pagekite.d/80_http.rc/service_on'

    >>> get_augeas_servicefile_path('https')
    '/files/etc/pagekite.d/443_https.rc/service_on'

    >>> get_augeas_servicefile_path('http/80')
    '/files/etc/pagekite.d/80_http.rc/service_on'

    >>> get_augeas_servicefile_path('http/8080')
    '/files/etc/pagekite.d/8080_http.rc/service_on'

    >>> get_augeas_servicefile_path('raw/22')
    '/files/etc/pagekite.d/22_raw.rc/service_on'

    >>> get_augeas_servicefile_path('xmpp')
    Traceback (most recent call last):
        ...
    ValueError: Unsupported protocol: xmpp

    """
    if not protocol.startswith(("http", "https", "raw")):
        raise ValueError('Unsupported protocol: %s' % protocol)

    try:
        _protocol, port = protocol.split('/')
    except ValueError:
        if protocol == 'http':
            relpath = '80_http.rc'
        elif protocol == 'https':
            relpath = '443_https.rc'
        else:
            raise ValueError('Unsupported protocol: %s' % protocol)
    else:
        relpath = '%s_%s.rc' % (port, _protocol)

    return os.path.join(CONF_PATH, relpath, 'service_on')


def update_names_module(is_enabled=None):
    """Update the PageKite domain and services of the 'names' module."""
    domain_removed.send_robust(sender='pagekite',
                               domain_type='domain-type-pagekite')

    if is_enabled is False:
        return

    if is_enabled is None and not app_module.App.get('pagekite').is_enabled():
        return

    from . import privileged
    config = privileged.get_config()
    enabled_services = [
        service for service, value in config['predefined_services'].items()
        if value
    ]
    if config['kite_name'] and config['kite_name'] != UNCONFIGURED_KITE:
        domain_added.send_robust(sender='pagekite',
                                 domain_type='domain-type-pagekite',
                                 name=config['kite_name'],
                                 services=enabled_services)
