# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Main FreedomBox views.
"""

import time

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from stronghold.decorators import public

from plinth import app, package
from plinth.daemon import app_is_running
from plinth.modules.config import get_advanced_mode
from plinth.translation import get_language_from_request, set_language

from . import forms, frontpage

REDIRECT_FIELD_NAME = 'next'


def _get_redirect_url_from_param(request):
    """Return the redirect URL from 'next' GET/POST param."""
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME, '')
    redirect_to = request.POST.get(REDIRECT_FIELD_NAME, redirect_to)
    if is_safe_url(url=redirect_to, allowed_hosts={request.get_host()}):
        return redirect_to

    return reverse('index')


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
        return _get_redirect_url_from_param(self.request)


class AppView(FormView):
    """A generic view for showing an app's main page.

    The view and it's template may be customized but by default show the
    following:

    * Icon for the app
    * Name of the app
    * Description of the app
    * Link to the manual page for the app
    * A button to enable/disable the app
    * A toolbar with common actions such as 'Run diagnostics'
    * A status section showing the running status of the app
    * A form for configuring the app

    The following class properties are available on the view:

    'app_id' is the mandatory property to set the ID of the app. It is used to
    retrieve the App instance for the app that is needed for basic information
    and operations such as enabling/disabling the app.

    'form_class' is the Django form class that is used by this view. By default
    the AppForm class is used.

    'template_name' is the template used to render this view. By default it is
    app.html. It may be overridden with a template that derives from app.html
    to customize the appearance of the app to achieve more complex presentation
    instead of the simple appearance provided by default.

    'port_forwarding_info' is a list of port information dictionaries that can
    used to show a special section in the app page that tells the users how to
    forward ports on their router for this app to work properly.

    """
    form_class = forms.AppForm
    app_id = None
    template_name = 'app.html'
    port_forwarding_info = None

    def __init__(self, *args, **kwargs):
        """Initialize the view."""
        super().__init__(*args, **kwargs)
        self._common_status = None

    @property
    def success_url(self):
        return self.request.path

    @property
    def app(self):
        """Return the app for which this view is configured."""
        if not self.app_id:
            raise ImproperlyConfigured('Missing attribute: app_id')

        return app.App.get(self.app_id)

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
        context['app_id'] = self.app.app_id
        context['is_running'] = app_is_running(self.app)
        context['app_info'] = self.app.info
        context['has_diagnostics'] = self.app.has_diagnostics()
        context['port_forwarding_info'] = self.port_forwarding_info

        from plinth.modules.firewall.components import Firewall
        context['firewall'] = self.app.get_components_of_type(Firewall)

        return context


class SetupView(TemplateView):
    """View to prompt and setup applications."""
    template_name = 'setup.html'

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super(SetupView, self).get_context_data(**kwargs)
        setup_helper = self.kwargs['setup_helper']
        context['setup_helper'] = setup_helper
        context['app_info'] = setup_helper.module.app.info

        # Reuse the value of setup_state throughout the view for consistency.
        context['setup_state'] = setup_helper.get_state()
        context['setup_current_operation'] = setup_helper.current_operation

        # Perform expensive operation only if needed
        if not context['setup_current_operation']:
            context[
                'package_manager_is_busy'] = package.is_package_manager_busy()

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


def notification_dismiss(request, id):
    """Dismiss a notification."""
    from .notification import Notification
    notes = Notification.list(key=id, user=request.user)
    if not notes:
        raise Http404

    notes[0].dismiss()

    return HttpResponseRedirect(_get_redirect_url_from_param(request))
