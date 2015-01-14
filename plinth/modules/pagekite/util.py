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

from django.contrib import messages
from gettext import gettext as _
import logging

from actions.pagekite_common import construct_params, deconstruct_params
from plinth import actions

LOGGER = logging.getLogger(__name__)


PREDEFINED_SERVICES = {
    'http': {
        'params': {'protocol': 'http',
                   'kitename': '@kitename',
                   'backend_port': '80',
                   'backend_host': 'localhost',
                   'secret': '@kitesecret'},
        'label': _("Web Server (HTTP)"),
        'help_text': _("Site will be available at "
                       "<a href=\"http://{0}\">http://{0}</a>"),
    },
    'https': {
        'params': {'protocol': 'https',
                   'kitename': '@kitename',
                   'backend_port': '443',
                   'backend_host': 'localhost',
                   'secret': '@kitesecret'},
        'label': _("Web Server (HTTPS)"),
        'help_text': _("Site will be available at "
                       "<a href=\"https://{0}\">https://{0}</a>"),
    },
    'ssh': {
        'params': {'protocol': 'raw/22',
                   'kitename': '@kitename',
                   'backend_port': '22',
                   'backend_host': 'localhost',
                   'secret': '@kitesecret'},
        'label': _("Secure Shell (SSH)"),
        'help_text': _("See SSH client setup <a href=\""
                       "https://pagekite.net/wiki/Howto/SshOverPageKite/\">"
                       "instructions</a>")
    },
}


def get_status():
    """
    Return the current status of PageKite configuration by
    executing various actions.
    """
    status = {}

    # PageKite service enabled/disabled
    output = _run(['is-enabled'])
    status['enabled'] = (output.split()[0] == 'yes')

    # PageKite kite details
    output = _run(['get-kite'])
    kite_details = output.split()
    status['kite_name'] = kite_details[0]
    status['kite_secret'] = kite_details[1]

    # PageKite server: 'pagekite.net' if flag 'defaults' is set,
    # the value of 'frontend' otherwise
    use_pagekitenet_server = _run(['get-pagekitenet-frontend-status'])
    if "enabled" in use_pagekitenet_server:
        value = 'pagekite.net'
    elif "disabled" in use_pagekitenet_server:
        value = _run(['get-frontend'])
    status['server'] = value.replace('\n', '')

    # Service status
    status.update(get_enabled_services())
    return status


def get_enabled_services():
    """Get enabled services as used by the ConfigureForm, which is:

    {'http': False, 'ssh': True, 'custom': {'http/888': {'protocol': 'http', }}
    """
    services = {'custom_services': {}}
    # set all predefined services to 'disabled' by default
    [services.update({proto: False}) for proto in PREDEFINED_SERVICES.keys()]
    # now, search for the enabled ones
    for serviceline in _run(['get-services']).split():
        params = construct_params(serviceline)
        for name, predefined_service in PREDEFINED_SERVICES.items():
            if params == predefined_service['params']:
                services[name] = True
                break
        else:
            services['custom_services'][params['protocol']] = params
    return services


# TODO: deprecated
def _apply_changes(request, old_status, new_status):
    """Apply the changes to PageKite configuration"""
    LOGGER.info('New status is - %s', new_status)

    if old_status != new_status:
        _run(['stop'])

    if old_status['enabled'] != new_status['enabled']:
        if new_status['enabled']:
            _run(['enable'])
            messages.success(request, _('PageKite enabled'))
        else:
            _run(['disable'])
            messages.success(request, _('PageKite disabled'))

    if old_status['kite_name'] != new_status['kite_name'] or \
            old_status['kite_secret'] != new_status['kite_secret']:
        _run(['set-kite', '--kite-name', new_status['kite_name'],
              '--kite-secret', new_status['kite_secret']])
        messages.success(request, _('Kite details set'))

    if old_status['server'] != new_status['server']:
        server = new_status['server']
        if server in ('defaults', 'default', 'pagekite.net'):
            _run(['enable-pagekitenet-frontend'])
        else:
            _run(['set-frontend', server])
        messages.success(request, _('Pagekite server set'))

    for service in PREDEFINED_SERVICES.keys():
        if old_status[service] != new_status[service]:
            params = PREDEFINED_SERVICES[service]
            param_string = deconstruct_params(params)
            if new_status[service]:
                _run(['enable-service', param_string])
                messages.success(request, _('Service enabled: {service}')
                                 .format(service=service))
            else:
                _run(['disable-service', param_string])
                messages.success(request, _('Service disabled: {service}')
                                 .format(service=service))

    if old_status != new_status:
        _run(['start'])


def _run(arguments, superuser=True):
    """Run a given command and raise exception if there was an error"""
    command = 'pagekite'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
