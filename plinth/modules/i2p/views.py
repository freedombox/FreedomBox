# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for I2P application.
"""

from django.utils.translation import gettext_lazy as _

from plinth.views import AppView


class I2PAppView(AppView):
    """Serve configuration page."""
    app_id = 'i2p'
    template_name = 'i2p.html'
    proxies_description = [
        _('I2P lets you browse the Internet and hidden services (eepsites) '
          'anonymously. For this, your browser, preferably the Tor Browser, '
          'needs to be configured with a proxy.'),
        _('By default HTTP, HTTPS and IRC proxies are available. Additional '
          'proxies and tunnels may be configured using the tunnel '
          'configuration interface.'),
    ]
    torrents_description = [
        _('I2P provides an application to download files anonymously in a '
          'peer-to-peer network. Download files by adding torrents or '
          'create a new torrent to share a file.'),
    ]

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        context['proxies_description'] = self.proxies_description
        context['torrents_description'] = self.torrents_description

        return context
