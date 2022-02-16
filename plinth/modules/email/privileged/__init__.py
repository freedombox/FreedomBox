# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Provides privileged actions that run as root.
"""

from . import aliases, dkim, domain, home, postfix, spam, tls

__all__ = ['aliases', 'domain', 'dkim', 'home', 'postfix', 'spam', 'tls']
