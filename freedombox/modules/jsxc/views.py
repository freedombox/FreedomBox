# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the JSXC module."""

import copy

from django.http import Http404
from django.views.generic import TemplateView

import plinth.app as app_module
from plinth.middleware import CONTENT_SECURITY_POLICY
from plinth.modules.names.components import DomainName


class JsxcView(TemplateView):
    """A simple page to embed Javascript XMPP Client library."""

    template_name = 'jsxc_launch.html'
    headers: dict[str, str] = {}

    def __init__(self, **kwargs):
        """Initialize the view and set CSP."""
        super().__init__(**kwargs)
        csp = copy.copy(CONTENT_SECURITY_POLICY)
        csp['style-src'] = "'self' 'unsafe-inline'"
        self.headers['Content-Security-Policy'] = csp.get_header_value()

    def dispatch(self, request, *args, **kwargs):
        """Don't serve the view when app is disabled."""
        app = app_module.App.get('jsxc')
        if not app.is_enabled():
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs) -> dict[str, object]:
        """Add domain information to view context."""
        context = super().get_context_data(*args, **kwargs)
        context['domain_name'] = DomainName.list_names()[0]
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET request and return a response object."""
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, headers=self.headers)
