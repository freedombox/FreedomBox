#
# This file is part of Plinth.
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

from gettext import gettext as _
import logging
import shlex

from plinth import actions

LOGGER = logging.getLogger(__name__)

# defaults for the credentials; @kitename acts as a placeholder and is
# understood (and replaced with the actual kitename) by pagekite.
BACKEND_HOST = 'localhost'
KITE_NAME = '@kitename'
KITE_SECRET = '@kitesecret'

SERVICE_PARAMS = ['protocol', 'kitename', 'backend_host', 'backend_port',
                  'secret']

# Predefined services are used to build the PredefinedServiceForm
#
# ATTENTION: When changing the params, make sure that the AddCustomServiceForm
# still recognizes when you try to add a service equal to a predefined one
PREDEFINED_SERVICES = {
    'http': {
        'params': {'protocol': 'http',
                   'kitename': KITE_NAME,
                   'backend_port': '80',
                   'backend_host': BACKEND_HOST,
                   'secret': KITE_SECRET},
        'label': _("Web Server (HTTP)"),
        'help_text': _("Site will be available at "
                       "<a href=\"http://{0}\">http://{0}</a>"),
    },
    'https': {
        'params': {'protocol': 'https',
                   'kitename': KITE_NAME,
                   'backend_port': '443',
                   'backend_host': BACKEND_HOST,
                   'secret': KITE_SECRET},
        'label': _("Web Server (HTTPS)"),
        'help_text': _("Site will be available at "
                       "<a href=\"https://{0}\">https://{0}</a>"),
    },
    'ssh': {
        'params': {'protocol': 'raw/22',
                   'kitename': KITE_NAME,
                   'backend_port': '22',
                   'backend_host': BACKEND_HOST,
                   'secret': KITE_SECRET},
        'label': _("Secure Shell (SSH)"),
        'help_text': _("See SSH client setup <a href=\""
                       "https://pagekite.net/wiki/Howto/SshOverPageKite/\">"
                       "instructions</a>")
    },
}


def convert_to_service(service_string):
    """ Convert a service string into a service parameter dictionary
    >>> convert_to_service('https/443:@kitename:localhost:443:@kitesecret')
    {'kitename': '@kitename', 'backend_host': 'localhost', \
'secret': '@kitesecret', 'protocol': 'https/443', 'backend_port': '443'}
    """
    # The actions.py uses shlex.quote() to escape/quote malicious user input.
    # That affects '*.@kitename', so the params string gets quoted.
    # If the string is escaped and contains '*.@kitename', look whether shlex
    # would still quote/escape the string when we remove '*.@kitename'.

    if service_string.startswith("'") and service_string.endswith("'"):
        unquoted_string = service_string[1:-1]
        error_msg = "The parameters contain suspicious characters: %s "
        if '*.@kitename' in service_string:
            unquoted_test_string = unquoted_string.replace('*.@kitename', '')
            if unquoted_test_string == shlex.quote(unquoted_test_string):
                # no other malicious characters found, use the unquoted string
                service_string = unquoted_string
            else:
                raise RuntimeError(error_msg % service_string)
        else:
            raise RuntimeError(error_msg % service_string)

    try:
        params = dict(zip(SERVICE_PARAMS, service_string.split(':')))
    except Exception:
        msg = """params are expected to be a ':'-separated string containing
              values for: %s , for example:\n"--params
              http/8000:@kitename:localhost:8000:@kitesecret"
              """
        raise ValueError(msg % ", ".join(SERVICE_PARAMS))
    return params


def convert_service_to_string(service):
    """ Convert service dict into a ":"-separated parameter string

    >>> convert_service_to_string({'kitename': '@kitename', \
'backend_host': 'localhost', 'secret': '@kitesecret', \
'protocol': 'https/443', 'backend_port': '443'})
    'https/443:@kitename:localhost:443:@kitesecret'
    """
    try:
        service_string = ":".join([str(service[param]) for param in
                                  SERVICE_PARAMS])
    except KeyError:
        raise ValueError("Could not parse params: %s " % service)
    return service_string


def get_kite_details():
    output = _run(['get-kite'])
    kite_details = output.split()
    return {'kite_name': kite_details[0],
            'kite_secret': kite_details[1]}


def get_pagekite_config():
    """
    Return the current PageKite configuration by executing various actions.
    """
    status = {}

    # PageKite service enabled/disabled
    # This assumes that if pagekite is running it's also enabled as a service
    output = _run(['is-running'])
    status['enabled'] = (output.split()[0] == 'yes')

    # PageKite kite details
    status.update(get_kite_details())

    # PageKite frontend server
    server = _run(['get-frontend'])
    status['server'] = server.replace('\n', '')

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
    for serviceline in _run(['get-services']).split():
        service = convert_to_service(serviceline)
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


def _run(arguments, superuser=True):
    """Run a given command and raise exception if there was an error"""
    command = 'pagekite'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
