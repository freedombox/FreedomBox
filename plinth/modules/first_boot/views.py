#
# This file is part of Plinth.
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

from django import http
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from plinth import network
from plinth.modules import first_boot


class WelcomeView(TemplateView):
    """Show the welcome screen."""

    template_name = 'firstboot_welcome.html'

    def post(self, request, *args, **kwargs):
        """On POST, mark this step as done and move to next step."""
        first_boot.mark_step_done('firstboot_welcome')
        return http.HttpResponseRedirect(reverse(first_boot.next_step()))


class CompleteView(TemplateView):
    """Show summary after all firstboot setup is done.

    After viewing this page the firstboot module can't be accessed anymore.
    """

    template_name = 'firstboot_complete.html'

    def get(self, request, *args, **kwargs):
        """Mark as done as soon as page is served."""
        response = super().get(self, request, *args, **kwargs)
        first_boot.mark_step_done('firstboot_complete')
        return response

    def get_context_data(self, **kwargs):
        """Add network connections to context list."""
        context = super().get_context_data(**kwargs)
        context['connections'] = network.get_connection_list()
        context['title'] = _('Setup Complete')
        return context
