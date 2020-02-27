# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the JSXC module
"""

from django.views.generic import TemplateView

from plinth.modules import config
from plinth.views import AppView


class JSXCAppView(AppView):
    """Show ejabberd as an app."""
    app_id = 'jsxc'
    template_name = 'jsxc.html'
    show_status_block = False


class JsxcView(TemplateView):
    """A simple page to embed Javascript XMPP Client library."""
    template_name = 'jsxc_launch.html'

    def get_context_data(self, *args, **kwargs):
        """Add domain information to view context."""
        context = super().get_context_data(*args, **kwargs)
        context['domainname'] = config.get_domainname()
        return context
