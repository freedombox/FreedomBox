# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manfiest for letsencrypt.
"""

from plinth.modules.backups.api import validate as validate_backup

# XXX: Backup and restore the Apache site configuration.
backup = validate_backup({'secrets': {'directories': ['/etc/letsencrypt/']}})
