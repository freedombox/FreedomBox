# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manfiest for letsencrypt.
"""

# XXX: Backup and restore the Apache site configuration.
backup = {'secrets': {'directories': ['/etc/letsencrypt/']}}
