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
Main FreedomBox views.
"""

import time

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from stronghold.decorators import public

from plinth import package
from plinth.app import App
from plinth.daemon import app_is_running
from plinth.modules.config import get_advanced_mode
from plinth.translation import get_language_from_request, set_language

from . import forms, frontpage

REDIRECT_FIELD_NAME = 'next'


@public
def index(request):
    """Serve the main index page."""
    username = str(request.user) if request.user.is_authenticated else None
    shortcuts = frontpage.Shortcut.list(username)
    selected = request.GET.get('selected')

    selected_shortcut = [
        shortcut for shortcut in shortcuts if shortcut.component_id == selected
    ]
    selected_shortcut = selected_shortcut[0] if selected_shortcut else None

    from plinth.modules.storage import views as disk_views
    disk_views.warn_about_low_disk_space(request)

    return TemplateResponse(
        request, 'index.html', {
            'title': _('FreedomBox'),
            'shortcuts': shortcuts,
            'selected_shortcut': selected_shortcut,
        })


class AppsIndexView(TemplateView):
    """View for apps index"""
    template_name = 'apps.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['show_disabled'] = True
        context['advanced_mode'] = get_advanced_mode()
        return context


def system_index(request):
    """Serve the system index page."""
    from plinth.modules.storage import views as disk_views
    disk_views.warn_about_low_disk_space(request)
    return TemplateResponse(request, 'system.html',
                            {'advanced_mode': get_advanced_mode()})


class LanguageSelectionView(FormView):
    """View for language selection"""
    form_class = forms.LanguageSelectionForm
    template_name = 'language-selection.html'

    def get_initial(self):
        """Return the initial values for the form."""
        return {'language': get_language_from_request(self.request)}

    def form_valid(self, form):
        """Set or reset the current language."""
        response = super().form_valid(form)
        set_language(self.request, response, form.cleaned_data['language'])
        return response

    def get_success_url(self):
        """Return the URL in the next parameter or home page."""
        redirect_to = self.request.GET.get(REDIRECT_FIELD_NAME, '')
        redirect_to = self.request.POST.get(REDIRECT_FIELD_NAME, redirect_to)
        if is_safe_url(url=redirect_to,
                       allowed_hosts={self.request.get_host()}):
            return redirect_to

        return reverse('index')


class AppView(FormView):
    """A generic view for configuring simple apps."""
    clients = []
    name = None
    # List of paragraphs describing the service
    description = ""
    form_class = forms.AppForm
    # Display the 'status' block of the app.html template
    # This block uses information from service.is_running. This method is
    # optional, so allow not showing this block here.
    show_status_block = True
    app_id = None
    template_name = 'app.html'
    manual_page = ''
    port_forwarding_info = None
    icon_filename = ''

    def __init__(self, *args, **kwargs):
        """Initialize the view."""
        super().__init__(*args, **kwargs)
        self._common_status = None

        if not self.name:
            raise ImproperlyConfigured('Missing name attribute')

    @property
    def success_url(self):
        return self.request.path

    @property
    def app(self):
        """Return the app for which this view is configured."""
        if not self.app_id:
            raise ImproperlyConfigured('Missing attribute: app_id')

        return App.get(self.app_id)

    def _get_common_status(self):
        """Return the status needed for form and template.

        Avoid multiple queries to expensive operations such as
        app.is_enabled().

        """
        if self._common_status:
            return self._common_status

        self._common_status = {'is_enabled': self.app.is_enabled()}
        return self._common_status

    def get_initial(self):
        """Return the status of the app to fill in the form."""
        return self._get_common_status()

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
                self.app.enable()
                messages.success(self.request, _('Application enabled'))
            else:
                self.app.disable()
                messages.success(self.request, _('Application disabled'))

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        """Add service to the context data."""
        context = super().get_context_data(*args, **kwargs)
        context.update(self._get_common_status())
        context['app'] = self.app
        context['app_id'] = self.app.app_id
        context['is_running'] = app_is_running(self.app)
        context['clients'] = self.clients
        context['name'] = self.name
        context['description'] = self.description
        context['has_diagnostics'] = self.app.has_diagnostics()
        context['show_status_block'] = self.show_status_block
        context['manual_page'] = self.manual_page
        context['port_forwarding_info'] = self.port_forwarding_info
        context['icon_filename'] = self.icon_filename

        from plinth.modules.firewall.components import Firewall
        context['firewall'] = self.app.get_components_of_type(Firewall)

        return context


class SetupView(TemplateView):
    """View to prompt and setup applications."""
    template_name = 'setup.html'
    name = 'None'
    # List of paragraphs describing the service
    description = []

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super(SetupView, self).get_context_data(**kwargs)
        setup_helper = self.kwargs['setup_helper']
        context['setup_helper'] = setup_helper

        # Reuse the value of setup_state throughout the view for consistency.
        context['setup_state'] = setup_helper.get_state()
        context['setup_current_operation'] = setup_helper.current_operation

        # Perform expensive operation only if needed
        if not context['setup_current_operation']:
            context[
                'package_manager_is_busy'] = package.is_package_manager_busy()

        context['name'] = self.name
        context['description'] = self.description

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'install' in request.POST:
                # Handle installing/upgrading applications.
                # Start the application setup, and refresh the page every few
                # seconds to keep displaying the status.
                self.kwargs['setup_helper'].run_in_thread()

                # Give a moment for the setup process to start and show
                # meaningful status.
                time.sleep(1)
                response = self.render_to_response(self.get_context_data())
                # Post/Response/Get pattern for reloads
                response.status_code = 303
                return response

            if 'refresh-packages' in request.POST:
                # Refresh apt package lists
                package.refresh_package_lists()
                return self.render_to_response(self.get_context_data())

        return super(SetupView, self).dispatch(request, *args, **kwargs)
