# SPDX-License-Identifier: AGPL-3.0-or-later

from plinth.modules import quassel
from plinth.views import AppView

from .forms import QuasselForm


class QuasselAppView(AppView):
    app_id = 'quassel'
    port_forwarding_info = quassel.port_forwarding_info
    form_class = QuasselForm

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

        return super().form_valid(form)
