# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for upgrades.
"""

from django.utils.translation import gettext_lazy as _

backup = {'config': {'files': ['/etc/apt/apt.conf.d/20auto-upgrades']}}

tags = [_('Security'), _('Automatic'), _('Reboots'), _('New features')]
