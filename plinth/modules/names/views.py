# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for name services.
"""

from plinth.views import AppView

from . import components


class NamesAppView(AppView):
    """Show names app main page."""

    app_id = 'names'
    template_name = 'names.html'

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['status'] = get_status()
        return context


def get_status():
    """Get configured services per name."""
    domains = components.DomainName.list()
    used_domain_types = {domain.domain_type for domain in domains}
    unused_domain_types = [
        domain_type for domain_type in components.DomainType.list().values()
        if domain_type not in used_domain_types
    ]

    return {'domains': domains, 'unused_domain_types': unused_domain_types}
