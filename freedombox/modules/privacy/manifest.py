# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for privacy app."""

from django.utils.translation import gettext_lazy as _

from . import privileged

backup = {'config': {'files': [str(privileged.CONFIG_FILE)]}}

tags = [_('Usage reporting'), _('External services'), _('Fallback DNS')]
