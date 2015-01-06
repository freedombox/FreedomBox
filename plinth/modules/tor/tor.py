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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for configuring Tor
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from gettext import gettext as _

from plinth import actions
from plinth import cfg
from plinth import package


class TorForm(forms.Form):  # pylint: disable=W0232
    """Tor configuration form"""
    hs_enabled = forms.BooleanField(
        label=_('Enable Hidden Service'),
        required=False)


def init():
    """Initialize the Tor module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname('Tor', 'glyphicon-eye-close', 'tor:index', 30)


@login_required
@package.required('tor')
def index(request):
    """Service the index page"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = TorForm(request.POST, prefix='tor')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = TorForm(initial=status, prefix='tor')
    else:
        form = TorForm(initial=status, prefix='tor')

    return TemplateResponse(request, 'tor.html',
                            {'title': _('Tor Control Panel'),
                             'is_running': status['is_running'],
                             'tor_ports': status['ports'],
                             'tor_hs_enabled': status['hs_enabled'],
                             'tor_hs_hostname': status['hs_hostname'],
                             'tor_hs_ports': status['hs_ports'],
                             'form': form})


def get_status():
    """Return the current status"""
    is_running = actions.superuser_run('tor', ['is-running']).strip() == 'yes'

    output = actions.superuser_run('tor-get-ports')
    port_info = output.split('\n')
    ports = {}
    for line in port_info:
        try:
            (key, val) = line.split()
            ports[key] = val
        except ValueError:
            continue

    output = actions.superuser_run('tor', ['get-hs'])
    output = output.strip()
    if output == '':
        hs_enabled = False
        hs_hostname = 'Not Configured'
        hs_ports = ''
    elif output == 'error':
        hs_enabled = False
        hs_hostname = 'Not available (Run Tor at least once)'
        hs_ports = ''
    else:
        hs_enabled = True
        hs_info = output.split()
        hs_hostname = hs_info[0]
        hs_ports = hs_info[1]

    return {'is_running': is_running,
            'ports': ports,
            'hs_enabled': hs_enabled,
            'hs_hostname': hs_hostname,
            'hs_ports': hs_ports}


def _apply_changes(request, old_status, new_status):
    """Apply the changes"""
    if old_status['hs_enabled'] == new_status['hs_enabled']:
        messages.info(request, _('Setting unchanged'))
        return

    if new_status['hs_enabled']:
        messages.success(request, _('Tor hidden service enabled'))
        command = 'enable-hs'
    else:
        messages.success(request, _('Tor hidden service disabled'))
        command = 'disable-hs'

    actions.superuser_run('tor', [command])
