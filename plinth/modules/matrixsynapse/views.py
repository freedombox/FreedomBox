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
Views for the Matrix Synapse module.
"""

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from plinth import actions
from plinth import views
from plinth.modules import matrixsynapse
from plinth.modules.matrixsynapse.forms import MatrixSynapseForm
from plinth.utils import get_domain_names


class SetupView(FormView):
    """Show matrix-synapse setup page."""
    template_name = 'matrix-synapse-pre-setup.html'
    form_class = MatrixSynapseForm
    success_url = reverse_lazy('matrixsynapse:index')

    def form_valid(self, form):
        """Handle valid form submission."""
        domain_name = form.cleaned_data['domain_name']
        actions.superuser_run('matrixsynapse',
                              ['setup', '--domain-name', domain_name])

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        """Provide context data to the template."""
        context = super().get_context_data(**kwargs)

        context['title'] = matrixsynapse.title
        context['description'] = matrixsynapse.description
        context['domain_names'] = get_domain_names()

        return context


class ServiceView(views.ServiceView):
    """Show matrix-synapse service page."""
    service_id = matrixsynapse.managed_services[0]
    template_name = 'matrix-synapse.html'
    description = matrixsynapse.description
    diagnostics_module_name = 'matrixsynapse'

    def dispatch(self, request, *args, **kwargs):
        """Redirect to setup page if setup is not done yet."""
        if not matrixsynapse.is_setup():
            return redirect('matrixsynapse:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(**kwargs)
        context['domain_name'] = matrixsynapse.get_configured_domain_name()
        return context
