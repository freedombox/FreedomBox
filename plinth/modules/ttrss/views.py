# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.forms import TLSDomainForm
from plinth.modules import ttrss
from plinth.views import AppView


class TTRSSAppView(AppView):
    app_id = 'ttrss'
    form_class = TLSDomainForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['domain'] = ttrss.get_domain()
        return initial

    def form_valid(self, form):
        """Change the domain of TT-RSS app."""
        data = form.cleaned_data
        if ttrss.get_domain() != data['domain']:
            ttrss.set_domain(data['domain'])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
