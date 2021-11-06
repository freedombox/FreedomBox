# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.forms import TLSDomainForm
from plinth.modules import quassel
from plinth.views import AppView


class QuasselAppView(AppView):
    app_id = 'quassel'
    form_class = TLSDomainForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['domain'] = quassel.get_domain()
        return initial

    def form_valid(self, form):
        """Change the access control of Radicale service."""
        data = form.cleaned_data
        if quassel.get_domain() != data['domain']:
            quassel.set_domain(data['domain'])
            quassel.app.get_component(
                'letsencrypt-quassel').setup_certificates()
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
