# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for Coturn app."""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

import plinth.modules.coturn as coturn
from plinth import app as app_module
from plinth import views

from . import forms


class CoturnAppView(views.AppView):
    """Serve configuration page."""

    app_id = 'coturn'
    template_name = 'coturn.html'
    form_class = forms.CoturnForm

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['config'] = coturn.get_config()
        return context

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['domain'] = coturn.get_domain()
        return initial

    def form_valid(self, form):
        """Change the domain of Coturn service."""
        data = form.cleaned_data
        if coturn.get_domain() != data['domain']:
            coturn.set_domain(data['domain'])
            app = app_module.App.get('coturn')
            app.get_component('letsencrypt-coturn').setup_certificates()
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
