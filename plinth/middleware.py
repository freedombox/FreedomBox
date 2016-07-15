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
Django middleware to show pre-setup message and setup progress.
"""

from django.contrib import messages
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
import logging

import plinth
from plinth.package import PackageException
from . import views


logger = logging.getLogger(__name__)


class SetupMiddleware(object):
    """Show setup page or progress if setup is neccessary or running."""

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        """Handle a request as Django middleware request handler."""
        # Perform a URL resolution. This is slightly inefficient as
        # Django will do this resolution again.
        try:
            resolver_match = urlresolvers.resolve(request.path_info)
        except urlresolvers.Resolver404:
            return

        if not resolver_match.namespaces or not len(resolver_match.namespaces):
            # Requested URL does not belong to any application
            return

        module_name = resolver_match.namespaces[0]
        module = plinth.module_loader.loaded_modules[module_name]

        # Collect errors from any previous operations and show them
        if module.setup_helper.is_finished:
            exception = module.setup_helper.collect_result()
            if not exception:
                messages.success(request, _('Application installed.'))
            else:
                if isinstance(exception, PackageException):
                    error_string = getattr(exception, 'error_string',
                                           str(exception))
                    error_details = getattr(exception, 'error_details', '')
                    message = _('Error installing application: {string} '
                                '{details}').format(
                        string=error_string, details=error_details)
                else:
                    message = _('Error installing application: {error}') \
                        .format(error=exception)

                messages.error(request, message)

        # Check if application is up-to-date
        if module.setup_helper.get_state() == 'up-to-date':
            return

        view = views.SetupView.as_view()
        return view(request, setup_helper=module.setup_helper)
