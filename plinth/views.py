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

from plinth import package as package_module


def index(request):
    """Serve the main index page."""
    return HttpResponseRedirect(reverse('apps:index'))


class PackageInstallView(TemplateView):
    """View to prompt and install packages."""
    template_name = 'package_install.html'

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super(PackageInstallView, self).get_context_data(**kwargs)

        if 'packages_names' not in context:
            context['package_names'] = self.kwargs.get('package_names', [])
        context['packages'] = {
            package_name: package_module.packages_resolved[package_name]
            for package_name in context['package_names']}
        context['is_installing'] = \
            package_module.is_installing(context['package_names'])
        context['transactions'] = package_module.transactions

        return context

    def post(self, *args, **kwargs):
        """Handle installing packages

        Start the package installation, and refresh the page every x seconds to
        keep displaying PackageInstallView.get() with the installation status.
        """
        package_module.start_install(self.kwargs['package_names'],
                                     on_install=self.kwargs.get('on_install'))
        return self.render_to_response(self.get_context_data())
