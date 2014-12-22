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

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.views.generic.edit import FormView

from plinth import package as package_module
from plinth.forms import PackageInstallForm


def index(request):
    """Serve the main index page."""
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('apps:index'))

    return HttpResponseRedirect(reverse('help:about'))


class PackageInstallView(FormView):
    """View to prompt and install packages."""
    template_name = 'package_install.html'
    form_class = PackageInstallForm

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super(PackageInstallView, self).get_context_data(**kwargs)
        if 'packages_names' not in context:
            context['package_names'] = self.kwargs.get('package_names', [])

        # Package details must have been resolved before building the form
        context['packages'] = [package_module.packages_resolved[package_name]
                               for package_name in context['package_names']]
        context['is_installing'] = \
            package_module.is_installing(context['package_names'])
        context['transactions'] = package_module.transactions

        return context

    def get_initial(self):
        """Return the initial data to be filled in the form."""
        initial = super(PackageInstallView, self).get_initial()
        try:
            initial['package_names'] = ','.join(self.kwargs['package_names'])
        except KeyError:
            raise ImproperlyConfigured('Argument package_names must be '
                                       'provided to PackageInstallView')

        return initial

    def form_valid(self, form):
        """Handle successful validation of the form.

        Start the package installation and show this view again.
        """
        package_names = form.cleaned_data['package_names'].split(',')
        package_module.start_install(package_names)

        return self.render_to_response(
            self.get_context_data(package_names=package_names))
