#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Views for the JSXC module
"""

from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from stronghold.decorators import public

from plinth.modules import config, jsxc
from plinth.views import AppView


class JSXCAppView(AppView):
    """Show ejabberd as an app."""
    app_id = 'jsxc'
    template_name = 'jsxc.html'
    name = jsxc.name
    description = jsxc.description
    show_status_block = False
    clients = jsxc.clients
    icon_filename = jsxc.icon_filename


class JsxcView(TemplateView):
    """A simple page to embed Javascript XMPP Client library."""
    template_name = 'jsxc_launch.html'

    @method_decorator(public)
    def dispatch(self, *args, **kwargs):
        """Dispatch a get, post etc. request."""
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add domain information to view context."""
        context = super().get_context_data(*args, **kwargs)
        context['domainname'] = config.get_domainname()
        return context
