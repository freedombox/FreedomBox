# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for name services.
"""

from django.template.response import TemplateResponse

from plinth.modules import names

from . import components


def index(request):
    """Serve name services page."""
    status = get_status()

    return TemplateResponse(request, 'names.html', {
        'app_info': names.app.info,
        'status': status
    })


def get_status():
    """Get configured services per name."""
    domains = components.DomainName.list()
    used_domain_types = {domain.domain_type for domain in domains}
    unused_domain_types = [
        domain_type for domain_type in components.DomainType.list().values()
        if domain_type not in used_domain_types
    ]

    return {'domains': domains, 'unused_domain_types': unused_domain_types}
