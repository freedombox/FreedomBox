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
Views for the Matrix Synapse module.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from plinth import actions
from plinth.forms import DomainSelectionForm
from plinth.modules import matrixsynapse, names
from plinth.views import AppView

from . import get_public_registration_status
from .forms import MatrixSynapseForm


class SetupView(FormView):
    """Show matrix-synapse setup page."""
    template_name = 'matrix-synapse-pre-setup.html'
    form_class = DomainSelectionForm
    success_url = reverse_lazy('matrixsynapse:index')
    icon_filename = matrixsynapse.icon_filename
    title = matrixsynapse.name

    def form_valid(self, form):
        """Handle valid form submission."""
        matrixsynapse.setup_domain(form.cleaned_data['domain_name'])
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        """Provide context data to the template."""
        context = super().get_context_data(**kwargs)

        context['name'] = matrixsynapse.name
        context['description'] = matrixsynapse.description
        context['icon_filename'] = matrixsynapse.icon_filename
        context['domain_names'] = names.components.DomainName.list_names(
            'matrix-synapse-plinth')

        return context


class MatrixSynapseAppView(AppView):
    """Show matrix-synapse service page."""
    app_id = 'matrixsynapse'
    template_name = 'matrix-synapse.html'
    name = matrixsynapse.name
    description = matrixsynapse.description
    form_class = MatrixSynapseForm
    port_forwarding_info = matrixsynapse.port_forwarding_info
    icon_filename = matrixsynapse.icon_filename

    def dispatch(self, request, *args, **kwargs):
        """Redirect to setup page if setup is not done yet."""
        if not matrixsynapse.is_setup():
            return redirect('matrixsynapse:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['domain_name'] = matrixsynapse.get_configured_domain_name()
        context['clients'] = matrixsynapse.clients
        context['manual_page'] = matrixsynapse.manual_page
        context['certificate_status'] = matrixsynapse.get_certificate_status()
        return context

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update({
            'enable_public_registration': get_public_registration_status(),
        })
        return initial

    def form_valid(self, form):
        """Handle valid form submission."""
        old_config = self.get_initial()
        new_config = form.cleaned_data
        app_same = old_config['is_enabled'] == new_config['is_enabled']
        pubreg_same = old_config['enable_public_registration'] == \
            new_config['enable_public_registration']

        if app_same and pubreg_same:
            # TODO: find a more reliable/official way to check whether the
            # request has messages attached.
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        elif not app_same:
            if new_config['is_enabled']:
                self.app.enable()
            else:
                self.app.disable()

        if not pubreg_same:
            # note action public-registration restarts, if running now
            if new_config['enable_public_registration']:
                actions.superuser_run('matrixsynapse',
                                      ['public-registration', 'enable'])
                messages.success(self.request,
                                 _('Public registration enabled'))
            else:
                actions.superuser_run('matrixsynapse',
                                      ['public-registration', 'disable'])
                messages.success(self.request,
                                 _('Public registration disabled'))

        return super().form_valid(form)
