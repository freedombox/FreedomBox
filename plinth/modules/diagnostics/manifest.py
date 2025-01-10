# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for diagnostics.
"""

from django.utils.translation import gettext_lazy as _

backup: dict = {}

tags = [_('Detect problems'), _('Repair'), _('Daily')]
