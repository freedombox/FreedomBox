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

from actions.pagekite_util import construct_params
from plinth import actions

LOGGER = logging.getLogger(__name__)

# defaults for the credentials; @kitename acts as a placeholder and is
# understood (and replaced with the actual kitename) by pagekite.
KITE_NAME = '@kitename'
KITE_SECRET = '@kitesecret'
BACKEND_HOST = 'localhost'
# predefined services show up in the PredefinedServiceForm as checkbox
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


def get_kite_details():
    output = _run(['get-kite'])
    kite_details = output.split()
    return {'kite_name': kite_details[0],
            'kite_secret': kite_details[1]}


# TODO: deprecated?
def prepare_params_for_display(params):
    """Add extra information to display a custom service:

    - protocol is split into 'protocol' and 'frontend_port'
    - we try to detect whether 'subdomains' are supported (as boolean)
    """
    protocol = params['protocol']
    if '/' in protocol:
        params['protocol'], params['frontend_port'] = protocol.split('/')
    params['subdomains'] = params['kitename'].startswith('*.')
    return params


def prepare_params_for_storage(params):
    """Prepare the params from the custom service form for being stored

    - Merge the 'frontend_port' and 'protocol' entries into 'protocol'
    - Adapt the kitename if subdomains should be supported
    """
    if 'frontend_port' in params:
        params['protocol'] = "%s/%s" % (params['protocol'],
                                        params['frontend_port'])
        del params['frontend_port']

    if 'subdomains' in params:
        params['kitename'] = "*.%s" % params['kitename']
        del params['subdomains']

    return params


def get_pagekite_config():
    """
    Return the current PageKite configuration by executing various actions.
    """
    status = {}

    # PageKite service enabled/disabled
    output = _run(['is-enabled'])
    status['enabled'] = (output.split()[0] == 'yes')

    # PageKite kite details
    status.update(get_kite_details())

    # PageKite server: 'pagekite.net' if flag 'defaults' is set,
    # the value of 'frontend' otherwise
    use_pagekitenet_server = _run(['get-pagekitenet-frontend-status'])
    if "enabled" in use_pagekitenet_server:
        value = 'pagekite.net'
    elif "disabled" in use_pagekitenet_server:
        value = _run(['get-frontend'])
    status['server'] = value.replace('\n', '')

    return status


def get_pagekite_services():
    """Get enabled services. Returns two dictionaries:

    1. predefined services: {'http': False, 'ssh': True, 'https': True}
    2. custom services: [{'protocol': 'http', 'secret' 'nono', ..}, [..]}
    """
    custom = []
    predefined = {}
    # set all predefined services to 'disabled' by default
    [predefined.update({proto: False}) for proto in PREDEFINED_SERVICES.keys()]
    # now, search for the enabled ones
    for serviceline in _run(['get-services']).split():
        params = construct_params(serviceline)
        for name, predefined_service in PREDEFINED_SERVICES.items():
            if params == predefined_service['params']:
                predefined[name] = True
                break
        else:
            custom.append(prepare_params_for_display(params))
    return predefined, custom


def _run(arguments, superuser=True):
    """Run a given command and raise exception if there was an error"""
    command = 'pagekite'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
