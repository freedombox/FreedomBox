# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the JSXC module."""

from django.http import Http404
from django.views.generic import TemplateView

import plinth.app as app_module
from plinth.modules import names


class JsxcView(TemplateView):
    """A simple page to embed Javascript XMPP Client library."""

    template_name = 'jsxc_launch.html'

    def dispatch(self, request, *args, **kwargs):
        """Don't serve the view when app is disabled."""
        app = app_module.App.get('jsxc')
        if not app.is_enabled():
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add domain information to view context."""
        context = super().get_context_data(*args, **kwargs)
        context['domain_name'] = names.get_domain_name()
        return context
