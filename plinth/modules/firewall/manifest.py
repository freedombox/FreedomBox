# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for firewall.
"""

from django.utils.translation import gettext_lazy as _

backup: dict = {}

tags = [_('Ports'), _('Blocking'), _('Status'), _('Automatic')]
