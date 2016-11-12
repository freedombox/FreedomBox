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

from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from plinth import network
from .middleware import mark_step_done, next_step


class WelcomeView(TemplateView):
    """Show the welcome screen."""

    template_name = 'firstboot_welcome.html'

    def get_context_data(self, **kwargs):
        """Returns the context data for the template."""
        context = super(WelcomeView, self).get_context_data(**kwargs)
        mark_step_done('firstboot_welcome')
        context['next_url'] = next_step()
        return context


def complete(request):
    """Show summary after all firstboot setup is done.

    After viewing this page the firstboot module can't be accessed anymore.
    """
    # Make sure that a user exists before finishing firstboot
    if User.objects.all():
        mark_step_done('firstboot_complete')

    connections = network.get_connection_list()

    return render(request, 'firstboot_complete.html',
                  {'title': _('Setup Complete'),
                   'connections': connections})
