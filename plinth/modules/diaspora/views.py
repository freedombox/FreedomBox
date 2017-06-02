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
Views for the diaspora module
"""
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from plinth import actions
from plinth.modules import diaspora
from plinth.modules.diaspora.forms import DiasporaForm
from plinth.utils import get_domain_names
from plinth.views import ServiceView


class DiasporaSetupView(FormView):
    """Show diaspora setup page."""
    template_name = 'diaspora-pre-setup.html'
    form_class = DiasporaForm
    description = diaspora.description
    title = diaspora.title
    success_url = reverse_lazy('diaspora:index')

    def form_valid(self, form):
        domain_name = form.cleaned_data['domain_name']
        actions.superuser_run('diaspora',
                              ['setup', '--domain-name', domain_name])
        diaspora.add_shortcut()

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = self.description
        context['title'] = self.title
        context['domain_names'] = get_domain_names()

        return context


class DiasporaServiceView(ServiceView):
    """Show diaspora service page."""
    service_id = diaspora.managed_services[0]
    template_name = 'diaspora-post-setup.html'
    diagnostics_module_name = 'diaspora'

    def dispatch(self, request, *args, **kwargs):
        if not diaspora.is_setup():
            return redirect('diaspora:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain_name'] = diaspora.get_configured_domain_name()

        return context
