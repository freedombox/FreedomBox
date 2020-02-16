# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for I2P application.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.generic import TemplateView

import plinth.modules.i2p as i2p
from plinth.views import AppView

subsubmenu = [{
    'url': reverse_lazy('i2p:index'),
    'text': ugettext_lazy('Configure')
}, {
    'url': reverse_lazy('i2p:tunnels'),
    'text': ugettext_lazy('Proxies')
}, {
    'url': reverse_lazy('i2p:torrents'),
    'text': ugettext_lazy('Anonymous torrents')
}]


class I2PAppView(AppView):
    """Serve configuration page."""
    app_id = 'i2p'
    show_status_block = True
    template_name = 'i2p.html'

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        context['title'] = i2p.app.info.name
        context['app_info'] = i2p.app.info
        context['subsubmenu'] = subsubmenu
        context['port_forwarding_info'] = i2p.port_forwarding_info
        return context


class ServiceBaseView(TemplateView):
    """View to describe and launch a service."""
    service_description = None
    service_title = None
    service_path = None

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = super().get_context_data(**kwargs)
        context['title'] = i2p.app.info.name
        context['app_info'] = i2p.app.info
        context['subsubmenu'] = subsubmenu
        context['is_enabled'] = i2p.app.is_enabled()
        context['service_title'] = self.service_title
        context['service_path'] = self.service_path
        context['service_description'] = self.service_description
        return context


class TunnelsView(ServiceBaseView):
    """View to describe and launch tunnel configuration."""
    template_name = 'i2p_service.html'
    service_title = _('I2P Proxies and Tunnels')
    service_path = '/i2p/i2ptunnel/'
    service_description = [
        _('I2P lets you browse the Internet and hidden services (eepsites) '
          'anonymously. For this, your browser, preferably a Tor Browser, '
          'needs to be configured for a proxy.'),
        _('By default HTTP, HTTPS and IRC proxies are available. Additional '
          'proxies and tunnels may be configured using the tunnel '
          'configuration interface.'),
    ]


class TorrentsView(ServiceBaseView):
    """View to describe and launch I2P torrents application."""
    template_name = 'i2p_service.html'
    service_title = _('Anonymous Torrents')
    service_path = '/i2p/i2psnark/'
    service_description = [
        _('I2P provides an application to download files anonymously in a '
          'peer-to-peer network. Download files by adding torrents or '
          'create a new torrent to share a file.'),
    ]
