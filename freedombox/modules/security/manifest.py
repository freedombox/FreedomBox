# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for security.
"""

from django.utils.translation import gettext_lazy as _

backup = {'config': {'files': ['/etc/security/access.d/50freedombox.conf']}}

tags = [_('Automatic bans'), _('Reports')]
