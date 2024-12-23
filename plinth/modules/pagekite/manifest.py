# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for pagekite.
"""

from django.utils.translation import gettext_lazy as _

backup = {
    'config': {
        'directories': ['/etc/pagekite.d/']
    },
    'services': ['pagekite']
}

tags = [_('Tunneling'), _('NAT traversal'), _('Remote access')]
