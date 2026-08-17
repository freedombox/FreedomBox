# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for avahi.
"""

from django.utils.translation import gettext_lazy as _

# Services that intend to make themselves discoverable will drop files into
# /etc/avahi/services. Currently, we don't intend to make that customizable.
# There is no necessity for backup and restore. This manifest will ensure that
# avahi enable/disable setting is preserved.
backup: dict = {}

tags = [_('Auto-discovery'), _('Local'), _('mDNS')]
