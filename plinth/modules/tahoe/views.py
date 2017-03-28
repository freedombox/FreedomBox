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
Views for the Tahoe-LAFS module
"""
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from plinth.forms import DomainSelectionForm
from plinth.modules import tahoe
from plinth.utils import get_domain_names
from plinth.views import ServiceView


class TahoeSetupView(FormView):
    """Show tahoe-lafs setup page."""
    template_name = 'tahoe-pre-setup.html'
    form_class = DomainSelectionForm
    description = tahoe.description
    title = tahoe.title
    success_url = reverse_lazy('tahoe:index')

    def form_valid(self, form):
        domain_name = form.cleaned_data['domain_name']
        tahoe.post_setup(domain_name)
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = self.description
        context['title'] = self.title
        context['domain_names'] = get_domain_names()

        return context


class TahoeServiceView(ServiceView):
    """Show tahoe-lafs service page."""
    service_id = tahoe.managed_services[0]
    template_name = 'tahoe-post-setup.html'
    description = tahoe.description
    diagnostics_module_name = 'tahoe'

    def dispatch(self, request, *args, **kwargs):
        if not tahoe.is_setup():
            return redirect('tahoe:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain_name'] = tahoe.get_configured_domain_name()
        context['introducers'] = tahoe.get_introducers()
        context['local_introducer'] = tahoe.get_local_introducer()

        return context


def add_introducer(request):
    if request.method == 'POST':
        tahoe.add_introducer((request.POST['pet_name'], request.POST['furl']))
        return redirect('tahoe:index')


def remove_introducer(request, introducer):
    if request.method == 'POST':
        tahoe.remove_introducer(introducer)
        return redirect('tahoe:index')
