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
"""
Views for the Ejabberd module
"""

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions
from plinth.modules import config, ejabberd
from plinth.views import AppView

from .forms import EjabberdForm


class EjabberdAppView(AppView):
    """Show ejabberd as a service."""
    app_id = 'ejabberd'
    template_name = 'ejabberd.html'
    name = ejabberd.name
    description = ejabberd.description
    diagnostics_module_name = 'ejabberd'
    form_class = EjabberdForm
    manual_page = ejabberd.manual_page
    port_forwarding_info = ejabberd.port_forwarding_info

    def get_initial(self):
        initdict = super().get_initial()
        initdict.update({'MAM_enabled': self.is_MAM_enabled()})
        return initdict

    def get_context_data(self, *args, **kwargs):
        """Add service to the context data."""
        context = super().get_context_data(*args, **kwargs)
        context['domainname'] = config.get_domainname()
        context['clients'] = ejabberd.clients
        return context

    def form_valid(self, form):
        """Enable/disable a service and set messages."""
        old_status = form.initial
        new_status = form.cleaned_data
        app_same = old_status['is_enabled'] == new_status['is_enabled']
        mam_same = old_status['MAM_enabled'] == new_status['MAM_enabled']

        if app_same and mam_same:
            # TODO: find a more reliable/official way to check whether the
            # request has messages attached.
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        elif not app_same:
            if new_status['is_enabled']:
                self.app.enable()
            else:
                self.app.disable()

        if not mam_same:
            # note ejabberd action "enable" or "disable" restarts, if running
            if new_status['MAM_enabled']:
                actions.superuser_run('ejabberd', ['mam', 'enable'])
                messages.success(self.request,
                                 _('Message Archive Management enabled'))
            else:
                actions.superuser_run('ejabberd', ['mam', 'disable'])
                messages.success(self.request,
                                 _('Message Archive Management disabled'))

        return super().form_valid(form)

    def is_MAM_enabled(self):
        """Return whether Message Archive Management (MAM) is enabled."""
        output = actions.superuser_run('ejabberd', ['mam', 'status'])
        return output.strip() == 'enabled'
