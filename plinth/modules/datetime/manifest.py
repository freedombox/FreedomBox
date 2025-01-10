# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for datetime.
"""

from django.utils.translation import gettext_lazy as _

backup = {
    'data': {
        'files': ['/etc/localtime']
    },
    'services': ['systemd-timedated'],
}

tags = [_('Network time'), _('Timezone')]
