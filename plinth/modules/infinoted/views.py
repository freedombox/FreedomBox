# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the infinoted app.
"""
from plinth.modules import infinoted
from plinth.views import AppView


class InfinotedAppView(AppView):
    """Main app view for Infinoted."""
    app_id = 'infinoted'
    port_forwarding_info = infinoted.port_forwarding_info
