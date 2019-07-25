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
},
              {
                  'url': reverse_lazy('i2p:torrents'),
                  'text': ugettext_lazy('Anonymous torrents')
              }]


class I2PAppView(AppView):
    """Serve configuration page."""
    app_id = 'i2p'
    clients = i2p.clients
    name = i2p.name
    description = i2p.description
    diagnostics_module_name = i2p.service_name
    show_status_block = True
    template_name = 'i2p.html'

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        context['title'] = i2p.name
        context['description'] = i2p.description
        context['clients'] = i2p.clients
        context['manual_page'] = i2p.manual_page
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
        context['title'] = i2p.name
        context['description'] = i2p.description
        context['clients'] = i2p.clients
        context['manual_page'] = i2p.manual_page
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
