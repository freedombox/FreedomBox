# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Errors for Tahoe-LAFS module
"""

from plinth.errors import PlinthError


class TahoeConfigurationError(PlinthError):
    """Tahoe-LAFS has not been configured for domain name."""
    pass
