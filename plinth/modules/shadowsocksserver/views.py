# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring Shadowsocks Server."""

import random
import string

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth import views

from . import privileged
from .forms import ShadowsocksServerForm


class ShadowsocksServerAppView(views.AppView):
    """Configuration view for Shadowsocks Server."""

    app_id = 'shadowsocksserver'
    form_class = ShadowsocksServerForm

    def get_initial(self, *args, **kwargs):
        """Get initial values for form."""
        status = super().get_initial()
        try:
            status.update(privileged.get_config())
        except Exception:
            # If we cannot read the configuration for some reason, generate a
            # new random password.
            password = ''.join(
                random.choice(string.ascii_letters) for _ in range(12))
            status.update({
                'password': password,
                'method': 'chacha20-ietf-poly1305',
            })

        return status

    def form_valid(self, form):
        """Configure Shadowsocks Server."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['password'] != new_status['password'] or \
           old_status['method'] != new_status['method']:
            privileged.merge_config(new_status['password'],
                                    new_status['method'])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
