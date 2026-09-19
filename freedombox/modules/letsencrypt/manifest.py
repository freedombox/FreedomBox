# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manfiest for letsencrypt.
"""

from django.utils.translation import gettext_lazy as _

# XXX: Backup and restore the Apache site configuration.
backup = {'secrets': {'directories': ['/etc/letsencrypt/']}}

tags = [_('Certificates'), _('HTTPS'), _('Web security'), _('Encryption')]
