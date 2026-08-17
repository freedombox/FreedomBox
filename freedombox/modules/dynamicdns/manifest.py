# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Dynamic DNS.
"""

from django.utils.translation import gettext_lazy as _

backup = {
    'config': {
        'directories': ['/etc/ez-ipupdate/']
    },
    'settings': [
        'dynamicdns_enable', 'dynamicdns_config', 'dynamicdns_status'
    ],
}

tags = [_('Domain'), _('Free'), _('Needs public IP')]
