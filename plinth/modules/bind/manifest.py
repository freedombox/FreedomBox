# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for bind.
"""

from django.utils.translation import gettext_lazy as _

backup = {
    'config': {
        'files': ['/etc/bind/named.conf.options']
    },
    'services': ['named']
}

tags = [
    _('Name server'),
    _('DNS resolver'),
]
