# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for storage.
"""
from django.utils.translation import gettext_lazy as _

backup: dict = {}

tags = [_('Disks'), _('Usage'), _('Auto-mount'), _('Expand partition')]
