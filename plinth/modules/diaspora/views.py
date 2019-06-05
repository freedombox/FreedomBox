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
Views for the diaspora module
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from plinth.forms import DomainSelectionForm
from plinth.modules import diaspora
from plinth.utils import get_domain_names
from plinth.views import AppView

from .forms import DiasporaAppForm


class DiasporaSetupView(FormView):
    """Show diaspora setup page."""
    template_name = 'diaspora-pre-setup.html'
    form_class = DomainSelectionForm
    description = diaspora.description
    title = diaspora.name
    success_url = reverse_lazy('diaspora:index')

    def form_valid(self, form):
        domain_name = form.cleaned_data['domain_name']
        diaspora.setup_domain_name(domain_name)

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = self.description
        context['title'] = self.title
        context['domain_names'] = get_domain_names()

        return context


class DiasporaAppView(AppView):
    """Show diaspora service page."""
    form_class = DiasporaAppForm
    app_id = 'diaspora'
    template_name = 'diaspora-post-setup.html'
    diagnostics_module_name = 'diaspora'
    name = diaspora.name

    def dispatch(self, request, *args, **kwargs):
        if not diaspora.is_setup():
            return redirect('diaspora:setup')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain_name'] = diaspora.get_configured_domain_name()
        context['clients'] = diaspora.clients
        return context

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        status = super().get_initial()
        status['is_user_registrations_enabled'] = \
            diaspora.is_user_registrations_enabled()
        return status

    def form_valid(self, form):
        """Enable/disable user registrations"""
        old_enabled = form.initial['is_enabled']
        new_enabled = form.cleaned_data['is_enabled']
        old_registration = form.initial['is_user_registrations_enabled']
        new_registration = form.cleaned_data['is_user_registrations_enabled']

        if old_registration == new_registration:
            if old_enabled == new_enabled:
                if not self.request._messages._queued_messages:
                    messages.info(self.request, _('Setting unchanged'))
        else:
            if new_registration:
                diaspora.enable_user_registrations()
                messages.success(self.request, _('User registrations enabled'))
            else:
                diaspora.disable_user_registrations()
                messages.success(self.request,
                                 _('User registrations disabled'))

        return super().form_valid(form)
