# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for avahi.
"""

from plinth.modules.backups.api import validate as validate_backup

# Services that intend to make themselves discoverable will drop files into
# /etc/avahi/services. Currently, we don't intend to make that customizable.
# There is no necessity for backup and restore. This manifest will ensure that
# avahi enable/disable setting is preserved.
backup = validate_backup({})
