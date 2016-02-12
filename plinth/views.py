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

"""
Main Plinth views
"""

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic import TemplateView
import time


def index(request):
    """Serve the main index page."""
    return HttpResponseRedirect(reverse('apps:index'))


class SetupView(TemplateView):
    """View to prompt and setup applications."""
    template_name = 'setup.html'

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super(SetupView, self).get_context_data(**kwargs)
        context['setup_helper'] = self.kwargs['setup_helper']
        return context

    def post(self, *args, **kwargs):
        """Handle installing/upgrading applications.

        Start the application setup, and refresh the page every few
        seconds to keep displaying the status.
        """
        self.kwargs['setup_helper'].run_in_thread()

        # Give a moment for the setup process to start and show
        # meaningful status.
        time.sleep(1)

        return self.render_to_response(self.get_context_data())
