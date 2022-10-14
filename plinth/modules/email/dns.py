# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Manage DNS entries needed for an email server.

See: https://en.wikipedia.org/wiki/MX_record
See: https://dmarcguide.globalcyberalliance.org/
See: https://support.google.com/a/answer/2466580
See: https://datatracker.ietf.org/doc/html/rfc6186
See: https://rspamd.com/doc/modules/dkim_signing.html
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class Entry:  # pylint: disable=too-many-instance-attributes
    """A DNS entry."""

    type_: str
    value: str
    domain: Union[str, None] = None
    class_: str = 'IN'
    ttl: int = 60
    priority: int = 10
    weight: Union[int, None] = None
    port: Union[int, None] = None

    def get_split_value(self):
        """If the record is TXT and value > 255, split it."""
        if len(self.value) <= 255:
            return self.value

        pieces = []
        value = self.value
        while value:
            pieces.append(f'"{value[:255]}"')
            value = value[255:]

        return ' '.join(pieces)


def get_entries():
    """Return the list of DNS entries to make."""
    from . import privileged

    domain = privileged.domain.get_domains()['primary_domain']
    mx_spam_entries = [
        Entry(type_='MX', value=f'{domain}.'),
        Entry(type_='TXT', value='v=spf1 mx a ~all'),
        Entry(
            domain='_dmarc', type_='TXT',
            value='v=DMARC1; p=none; sp=quarantine; '
            f'rua=mailto:postmaster@{domain}; ')
    ]
    try:
        dkim_public_key = privileged.get_dkim_public_key(domain)
        dkim_entries = [
            Entry(domain='dkim._domainkey', type_='TXT',
                  value=f'v=DKIM1; k=rsa; p={dkim_public_key}')
        ]
    except Exception:
        dkim_entries = []

    autoconfig_entries = [
        Entry(domain='_submission._tcp', type_='SRV', weight=10, port=587,
              value=f'{domain}.'),
        Entry(domain='_imaps._tcp', type_='SRV', weight=10, port=993,
              value=f'{domain}.'),
        Entry(domain='_pop3s._tcp', type_='SRV', priority=20, weight=10,
              port=995, value=f'{domain}.'),
    ]
    return mx_spam_entries + dkim_entries + autoconfig_entries
