# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for snapshot.
"""

from django.utils.translation import gettext_lazy as _

backup = {
    'config': {
        'files': ['/etc/snapper/configs/root', '/etc/default/snapper']
    }
}

tags = [_('Periodic'), _('Restore'), _('Known good state'), _('Btrfs')]
