# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure a firewall."""

from plinth import views
from plinth.modules import firewall

from . import components


class FirewallAppView(views.AppView):
    """Serve firewall index page."""

    app_id = 'firewall'
    template_name = 'firewall.html'

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for the template."""
        context = super().get_context_data(*args, **kwargs)
        context['components'] = components.Firewall.list()
        internal_enabled_ports = firewall.get_enabled_services(zone='internal')
        external_enabled_ports = firewall.get_enabled_services(zone='external')
        context['internal_enabled_ports'] = internal_enabled_ports
        context['external_enabled_ports'] = external_enabled_ports
        return context
