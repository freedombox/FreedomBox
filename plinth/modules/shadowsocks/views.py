# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring Shadowsocks."""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth import views

from . import privileged
from .forms import ShadowsocksForm


class ShadowsocksAppView(views.AppView):
    """Configuration view for Shadowsocks local socks5 proxy."""

    app_id = 'shadowsocks'
    form_class = ShadowsocksForm

    def get_initial(self, *args, **kwargs):
        """Get initial values for form."""
        status = super().get_initial()
        try:
            status.update(privileged.get_config())
        except Exception:
            status.update({
                'server': '',
                'server_port': 8388,
                'password': '',
                'method': 'chacha20-ietf-poly1305',
            })

        return status

    def form_valid(self, form):
        """Configure Shadowsocks."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['server'] != new_status['server'] or \
           old_status['server_port'] != new_status['server_port'] or \
           old_status['password'] != new_status['password'] or \
           old_status['method'] != new_status['method']:
            new_config = {
                'local_address': '::0',
                'local_port': 1080,
                'server': new_status['server'],
                'server_port': new_status['server_port'],
                'password': new_status['password'],
                'method': new_status['method'],
            }

            privileged.merge_config(new_config)
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
