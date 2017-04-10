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
Views for BIND module.
"""

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.views import ServiceView


from . import description, managed_services, get_default
from .forms import BindForm


class BindServiceView(ServiceView): # pylint: disable=too-many-ancestors
    """A specialized view for configuring Bind."""
    service_id = managed_services[0]
    diagnostics_module_name = "bind"
    description = description
    show_status_block = True
    form_class = BindForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(get_default())
        return initial

    def form_valid(self, form):
        """Change the configurations of Bind service."""
        data = form.cleaned_data
        old_config = get_default()

        if old_config['set_forwarding'] != data['set_forwarding']:
            value = 'true' if data['set_forwarding'] else 'false'
            actions.superuser_run(
                'bind',
                ['configure', '--set-forwarding', value])
            messages.success(self.request,
                             _('Set forwarding configuration updated'))

        if old_config['enable_dnssec'] != data['enable_dnssec']:
            value = 'true' if data['enable_dnssec'] else 'false'
            actions.superuser_run(
                'bind',
                ['configure', '--enable-dnssec', value])
            messages.success(self.request,
                             _('Enable DNSSEC configuration updated'))

        if old_config['forwarders'] != data['forwarders'] \
           and old_config['forwarders'] is not '':
            actions.superuser_run(
                'bind',
                ['dns', '--set', data['forwarders']])
            messages.success(self.request,
                             _('DNS server configuration updated'))
        elif old_config['forwarders'] is '' \
             and old_config['forwarders'] != data['forwarders']:
            messages.error(
                self.request,
                _('Enable forwarding to set forwarding DNS servers'))

        return super().form_valid(form)
