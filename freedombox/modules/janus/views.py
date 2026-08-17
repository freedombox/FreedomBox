# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the Janus app.
"""

import copy

from django.views.generic import TemplateView

from plinth import app as app_module
from plinth.middleware import CONTENT_SECURITY_POLICY


class JanusRoomView(TemplateView):
    """A simple page to host Janus video room."""
    template_name = 'janus_video_room.html'
    headers: dict[str, str] = {}

    def __init__(self, **kwargs):
        """Initialize the view and set CSP."""
        super().__init__(**kwargs)
        csp = copy.copy(CONTENT_SECURITY_POLICY)
        csp['script-src'] = "'self' 'unsafe-inline'"
        csp['style-src'] = "'self' 'unsafe-inline'"
        self.headers['Content-Security-Policy'] = csp.get_header_value()

    def get_context_data(self, *args, **kwargs):
        """Add user's TURN server information to view context."""
        app = app_module.App.get('janus')
        config = app.get_component('turn-janus').get_configuration()
        context = super().get_context_data(*args, **kwargs)
        context['user_turn_config'] = config.to_json()
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET request and return a response object."""
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, headers=self.headers)
