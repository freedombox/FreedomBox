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

import json
import logging
import os

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth.signals import domain_added, domain_removed

LOGGER = logging.getLogger(__name__)

# defaults for the credentials; @kitename acts as a placeholder and is
# understood (and replaced with the actual kitename) by pagekite.
BACKEND_HOST = 'localhost'
KITE_NAME = '@kitename'
KITE_SECRET = '@kitesecret'

# Augeas base path for Pagekite configuration files
CONF_PATH = '/files/etc/pagekite.d'

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


def get_kite_details():
    output = run(['get-kite'])
    kite_details = output.split()
    return {'kite_name': kite_details[0], 'kite_secret': kite_details[1]}


def get_pagekite_config():
    """
    Return the current PageKite configuration by executing various actions.
    """
    status = {}

    # PageKite service enabled/disabled
    # To enable PageKite two things are necessary:
    # 1) pagekite not being disabled in /etc/pagekite.d/10_account.rc
    # 2) the pagekite service running
    is_disabled = (run(['is-disabled']).strip() == 'true')
    service_running = action_utils.service_is_running('pagekite')
    status['enabled'] = service_running and not is_disabled

    # PageKite kite details
    status.update(get_kite_details())

    # PageKite frontend server
    server = run(['get-frontend']).strip()

    # Frontend entries are only considered valid if there's a ':' in
    # them otherwise, pagekite refuses to work, and we only set values
    # with ':'.
    if ':' in server:
        server_domain, server_port = server.split(':')
        status['server_domain'] = server_domain
        status['server_port'] = int(server_port)
    else:
        status['server_domain'] = server
        # No valid entry exists, default to port 80.  Hack: Return
        # string instead of int to force setting port on save
        status['server_port'] = '80'

    return status


def get_pagekite_services():
    """Get enabled services. Returns two values:

    1. predefined services: {'http': False, 'ssh': True, 'https': True}
    2. custom services: [{'protocol': 'http', 'secret' 'nono', ..}, [..]}
    """
    custom = []
    predefined = {}
    # set all predefined services to 'disabled' by default
    [predefined.update({proto: False}) for proto in PREDEFINED_SERVICES.keys()]
    # now, search for the enabled ones
    for serviceline in run(['get-services']).split('\n'):
        if not serviceline:  # skip empty lines
            continue

        service = json.loads(serviceline)
        for name, predefined_service in PREDEFINED_SERVICES.items():
            if service == predefined_service['params']:
                predefined[name] = True
                break
        else:
            custom.append(service)
    return predefined, custom


def prepare_service_for_display(service):
    """ Add extra information that is used when displaying a service

    - protocol is split into 'protocol' and 'frontend_port'
    - detect whether 'subdomains' are supported (as boolean)
    """
    protocol = service['protocol']
    if '/' in protocol:
        service['protocol'], service['frontend_port'] = protocol.split('/')
    service['subdomains'] = service['kitename'].startswith('*.')
    return service


def run(arguments, superuser=True, input=None):
    """Run a given command and raise exception if there was an error"""
    command = 'pagekite'

    if superuser:
        return actions.superuser_run(command, arguments, input=input)
    else:
        return actions.run(command, arguments, input=input)


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


def load_service(json_service):
    """ create a service out of json command-line argument

    1) parse json
    2) only use the parameters that we need (SERVICE_PARAMS)
    3) convert unicode to strings
    """
    service = json.loads(json_service)
    return dict((str(key), str(service[key])) for key in SERVICE_PARAMS)


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


def update_names_module(initial_registration=False, enabled=None,
                        kite_name=None):
    """
    Update the PageKite domain and services of the 'names' module.

    - initial_registration: Boolean (optional): Register also if not enabled
    - enabled: Boolean (optional) whether PageKite is enabled
    - kite_name: String (optional)
    """
    domain_removed.send_robust(sender='pagekite', domain_type='pagekite')

    if enabled is None:
        try:
            enabled = get_pagekite_config()['enabled']
        except IndexError:
            enabled = False

    if enabled:
        # Get enabled services and kite name
        services = get_pagekite_services()[0]
        enabled_services = [
            service for service in services if services[service]
        ]
        if kite_name is None:
            try:
                kite_name = get_kite_details()['kite_name']
            except IndexError:
                pass
    else:
        enabled_services = None
        kite_name = None

    if initial_registration or (enabled and kite_name):
        domain_added.send_robust(sender='pagekite', domain_type='pagekite',
                                 name=kite_name, description=_('Pagekite'),
                                 services=enabled_services)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
