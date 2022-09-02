# SPDX-License-Identifier: AGPL-3.0-or-later
"""Provides privileged actions that run as root."""

from .aliases import setup_aliases
from .dkim import get_dkim_public_key, setup_dkim
from .domain import set_domains
from .home import setup_home
from .postfix import setup_postfix
from .spam import setup_spam

__all__ = [
    'setup_aliases', 'get_dkim_public_key', 'setup_dkim', 'set_domains',
    'setup_home', 'setup_postfix', 'setup_spam'
]
