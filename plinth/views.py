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

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.template.response import TemplateResponse
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.utils.translation import ugettext as _
from stronghold.decorators import public
import time

from . import forms, frontpage
import plinth
from plinth import actions
from plinth import package
from plinth.modules.storage import views as disk_views


@public
def index(request):
    """Serve the main index page."""
    shortcuts = frontpage.get_shortcuts()
    selection = request.GET.get('selected')

    details, details_label, configure_url = None, None, None
    if selection in frontpage.shortcuts:
        details = frontpage.shortcuts[selection]['details']
        details_label = frontpage.shortcuts[selection]['label']
        configure_url = frontpage.shortcuts[selection]['configure_url']

    disk_views.warn_about_low_disk_space(request)

    return TemplateResponse(request, 'index.html',
                            {'title': _('FreedomBox'),
                             'shortcuts': shortcuts,
                             'selected_id': selection,
                             'details': details,
                             'details_label': details_label,
                             'configure_url': configure_url})


def system_index(request):
    """Serve the system index page."""
    disk_views.warn_about_low_disk_space(request)
    return TemplateResponse(request, 'system.html')


class ServiceView(FormView):
    """A generic view for configuring simple services."""
    service_id = None
    form_class = forms.ServiceForm
    template_name = 'service.html'
    # Set diagnostics_module_name to the module name to show diagnostics button
    diagnostics_module_name = ""
    # List of paragraphs describing the service
    description = ""
    # Display the 'status' block of the service.html template
    # This block uses information from service.is_running. This method is
    # optional, so allow not showing this block here.
    show_status_block = True

    @property
    def success_url(self):
        return self.request.path

    @property
    def service(self):
        if hasattr(self, '_service'):
            return self._service

        if not self.service_id:
            raise ImproperlyConfigured("missing attribute: 'service_id'")
        service = plinth.service.services.get(self.service_id, None)
        if service is None:
            message = "Could not find service %s" % self.service_id
            raise ImproperlyConfigured(message)
        self._service = service
        return service

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        return {'is_enabled': self.service.is_enabled(),
                'is_running': self.service.is_running()}

    def form_valid(self, form):
        """Enable/disable a service and set messages."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['is_enabled'] == new_status['is_enabled']:
            # TODO: find a more reliable/official way to check whether the
            # request has messages attached.
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        else:
            if new_status['is_enabled']:
                self.service.enable()
                messages.success(self.request, _('Application enabled'))
            else:
                self.service.disable()
                messages.success(self.request, _('Application disabled'))

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        """Add service to the context data."""
        context = super().get_context_data(*args, **kwargs)
        context['service'] = self.service
        if self.diagnostics_module_name:
            context['diagnostics_module_name'] = self.diagnostics_module_name
        if self.description:
            context['description'] = self.description
        context['show_status_block'] = self.show_status_block
        return context


class SetupView(TemplateView):
    """View to prompt and setup applications."""
    template_name = 'setup.html'

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super(SetupView, self).get_context_data(**kwargs)
        context['setup_helper'] = self.kwargs['setup_helper']
        context['package_manager_is_busy'] = package.is_package_manager_busy()
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
