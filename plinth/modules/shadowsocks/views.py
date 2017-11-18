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

"""
Plinth module for configuring Shadowsocks.
"""

import json
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from .forms import ShadowsocksForm
from plinth import actions
from plinth import views
from plinth.modules import shadowsocks

SHADOWSOCKS_CONFIG = '/etc/shadowsocks-libev/freedombox.json'


class ShadowsocksServiceView(views.ServiceView):
    """Configuration view for Shadowsocks local socks5 proxy."""
    service_id = 'shadowsocks'
    diagnostics_module_name = 'shadowsocks'
    form_class = ShadowsocksForm
    description = shadowsocks.description

    def get_initial(self, *args, **kwargs):
        """Get initial values for form."""
        try:
            configuration = open(SHADOWSOCKS_CONFIG, 'r').read()
            status = json.loads(configuration)
        except (OSError, json.JSONDecodeError):
            status = {
                'server': '',
                'server_port': 8388,
                'password': '',
                'method': 'chacha20-ietf-poly1305',
            }

        status['is_enabled'] = self.service.is_enabled()
        status['is_running'] = self.service.is_running()

        return status

    def form_valid(self, form):
        """Configure Shadowsocks."""
        old_status = form.initial
        new_status = form.cleaned_data

        if (old_status['server'] != new_status['server'] or
            old_status['server_port'] != new_status['server_port'] or
            old_status['password'] != new_status['password'] or
            old_status['method'] != new_status['method']):
            new_config = {
                'local_address': '::0',
                'local_port': 1080,
                'server': new_status['server'],
                'server_port': new_status['server_port'],
                'password': new_status['password'],
                'method': new_status['method'],
            }

            actions.superuser_run(
                'shadowsocks', ['merge-config'],
                input=json.dumps(new_config).encode())
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
