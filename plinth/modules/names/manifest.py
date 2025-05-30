# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for names.
"""

from django.utils.translation import gettext_lazy as _

backup: dict = {}

tags = [
    _('Domains'),
    _('Hostname'),
    _('DNS Resolution'),
]
