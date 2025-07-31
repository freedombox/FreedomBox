# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Main FreedomBox views.
"""

import random
import time
import traceback
import urllib.parse

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.forms import Form
from django.http import (Http404, HttpRequest, HttpResponseBadRequest,
                         HttpResponseRedirect, JsonResponse)
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from stronghold.decorators import public

from plinth import app as app_module
from plinth import menu
from plinth.daemon import app_is_running
from plinth.modules.config import get_advanced_mode
from plinth.modules.firewall.components import get_port_forwarding_info
from plinth.package import Packages
from plinth.translation import get_language_from_request, set_language

from . import forms, frontpage, operation, package, setup

REDIRECT_FIELD_NAME = 'next'


def is_safe_url(url):
    """Check if the URL is safe to redirect to.

    Based on Django internal utility removed in Django 4.0.

    """
    if url is not None:
        url = url.strip()

    if not url:
        return False

    if '\\' in url or url.startswith('///'):
        return False

    try:
        result = urllib.parse.urlparse(url)
    except ValueError:
        return False

    # Only accept URLs to the same site and scheme.
    if result.scheme or result.netloc:
        return False

    return True


def get_breadcrumbs(request: HttpRequest) -> dict[str, dict[str, str | bool]]:
    """Return all the URL ancestors that can be show as breadcrumbs."""
    breadcrumbs = {}

    def _add(url: str, name: str | None, url_name: str | None = None):
        """Add item into the breadcrumb dictionary."""
        breadcrumbs[url] = {
            'name': name,
            'is_active': request.path == url,
            'url_name': url_name
        }

    url_name = request.resolver_match.url_name
    full_url_name = ':'.join(request.resolver_match.app_names + [url_name])
    try:
        menu_item = menu.Menu.get_with_url_name(full_url_name)
    except LookupError:
        # There is no menu entry for this page, find it's app.
        _add(request.path, _('Here'), full_url_name)
        app_url_name = ':'.join(request.resolver_match.app_names + ['index'])
        try:
            menu_item = menu.Menu.get_with_url_name(app_url_name)
        except LookupError:
            # Don't know which app this page belongs to, assume parent is Home.
            menu_item = menu.Menu.get_with_url_name('index')

    for _number in range(10):
        _add(menu_item.url, menu_item.name, menu_item.url_name)
        if not menu_item.parent_url_name:
            # We have reached the top
            break

        menu_item = menu.Menu.get_with_url_name(menu_item.parent_url_name)
    else:
        # Too much hierarchy, we must be in a recursive loop.
        breadcrumbs = {}
        menu_item = menu.Menu.get_with_url_name('index')
        _add(menu_item.url, menu_item.name, menu_item.url_name)

    # Find the active section: 'index', 'apps', 'system' or 'help'.
    active_section_index = -2 if len(breadcrumbs) >= 2 else -1
    active_section_key = list(breadcrumbs.keys())[active_section_index]
    breadcrumbs[active_section_key]['is_active_section'] = True

    return breadcrumbs


def messages_error(request, message, exception):
    """Show an error message using Django messages framework.

    If an exception can show HTML message, handle is separately.
    """
    if hasattr(exception, 'get_html_message'):
        html_message = exception.get_html_message()
    else:
        exception_lines = traceback.format_exception(exception)
        html_message = ''.join(exception_lines)

    collapse_id = 'error-details-' + str(random.randint(0, 10**9))
    formatted_message = format_html(
        '{message} <a href="#" class="dropdown-toggle" '
        'data-bs-toggle="collapse" data-bs-target="#{collapse_id}" '
        'aria-expanded="false" aria-controls="{collapse_id}">'
        'Details</a><pre class="collapse" '
        'id="{collapse_id}"><code>{html_message}</code></pre>',
        message=message, html_message=html_message, collapse_id=collapse_id)
    messages.error(request, formatted_message)


def _get_redirect_url_from_param(request):
    """Return the redirect URL from 'next' GET/POST param."""
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME, '')
    redirect_to = request.POST.get(REDIRECT_FIELD_NAME, redirect_to)
    if is_safe_url(redirect_to):
        return redirect_to

    return reverse('index')


def _has_backup_restore(app):
    """Return whether an app implements backup/restore."""
    from plinth.modules.backups.components import BackupRestore
    return any([
        component.has_data
        for component in app.get_components_of_type(BackupRestore)
    ])


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


def _pick_menu_items(menu_items, selected_tags):
    """Return a sorted list of menu items filtered by tags."""

    class MenuProxy:
        """A proxy for the menu item to hold filtered children."""

        def __init__(self, menu_item: menu.Menu):
            """Initialize a menu proxy object."""
            self.menu_item = menu_item
            self.items: list[menu.Menu] = []
            tags = menu_item.tags or []
            for item in menu_item.items:
                tags += item.tags or []

            self.tags = list(tags)

        def __getattr__(self, name: str):
            """Return attributed from proxied object."""
            return getattr(self.menu_item, name)

    def _mismatch_map(menu_item) -> list[bool]:
        """Return a list of mismatches for selected tags.

        A mismatch is when a selected tag is *not* present in the list of
        tags for menu item.
        """
        menu_tags = set(menu_item.tags or [])
        return [tag not in menu_tags for tag in selected_tags]

    def _sort_key(menu_item):
        """Returns a comparable tuple to sort menu items.

        Sort items by tag match count first, then by the order of matched
        tags in user specified order, then by the order set by menu item,
        and then by the name of the menu item in current locale (by
        configured collation order).
        """
        return (_mismatch_map(menu_item).count(True), _mismatch_map(menu_item),
                menu_item.order, menu_item.name.lower())

    proxied_menu_items = []
    for menu_item in menu_items:
        proxied_item = MenuProxy(menu_item)
        proxied_item.items = _pick_menu_items(menu_item.items, selected_tags)
        proxied_menu_items.append(proxied_item)

    # Filter out menu items that don't match any of the selected tags. If
    # no tags are selected, return all menu items. Otherwise, return all
    # menu items that have at least one matching tag.
    filtered_menu_items = [
        menu_item for menu_item in proxied_menu_items
        if (not selected_tags) or (not all(_mismatch_map(menu_item)))
    ]

    return sorted(filtered_menu_items, key=_sort_key)


def _get_all_tags(menu_items: list[menu.Menu]) -> list[str]:
    """Return a sorted list of all tags present in the given menu items."""

    def get_tags(menu_items: list[menu.Menu]) -> set[str]:
        """Return a list of tags, unsorted."""
        all_tags = set()
        for menu_item in menu_items:
            all_tags.update(menu_item.tags or [])
            all_tags |= get_tags(menu_item.items)

        return all_tags

    # Sort tags by localized string
    return sorted(get_tags(menu_items), key=_)


class AppsIndexView(TemplateView):
    """View for apps index.

    This view supports filtering apps by one or more tags. If no tags are
    provided, it will show all the apps. If one or more tags are provided,
    it will select apps matching any of the provided tags.
    """
    template_name = 'apps.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['show_disabled'] = True
        context['advanced_mode'] = get_advanced_mode()

        tags = self.request.GET.getlist('tag', [])
        menu_items = menu.main_menu.active_item(self.request).items

        context['tags'] = tags
        context['all_tags'] = _get_all_tags(menu_items)
        context['menu_items'] = _pick_menu_items(menu_items, tags)

        return context


def system_index(request):
    """Serve the system index page."""
    tags = request.GET.getlist('tag', [])
    menu_items = menu.main_menu.active_item(request).items

    return TemplateResponse(
        request, 'system.html', {
            'advanced_mode': get_advanced_mode(),
            'menu_items': _pick_menu_items(menu_items, tags),
            'tags': tags,
            'all_tags': _get_all_tags(menu_items)
        })


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

    'form_class' is the Django form class that is used by this view. It may be
    None if the app does not have a configuration form. Default is None.

    'template_name' is the template used to render this view. By default it is
    app.html. It may be overridden with a template that derives from app.html
    to customize the appearance of the app to achieve more complex presentation
    instead of the simple appearance provided by default.

    """
    form_class: Form | None = None
    app_id: str | None = None
    template_name: str = 'app.html'

    def __init__(self, *args, **kwargs):
        """Initialize the view."""
        super().__init__(*args, **kwargs)
        self._common_status = None

    def dispatch(self, request, *args, **kwargs):
        """If operations are running on the app, use a different view."""
        operations = operation.manager.filter(self.app.app_id)
        if operations:
            view = AppOperationsView.as_view(app_id=self.app.app_id)
            return view(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle app enable/disable button separately."""
        if 'app_enable_disable_button' not in request.POST:
            return super().post(request, *args, **kwargs)

        form = forms.AppEnableDisableForm(data=self.request.POST)
        if form.is_valid():
            return self.enable_disable_form_valid(form)

        return HttpResponseBadRequest('Invalid form submission')

    @property
    def success_url(self):
        return self.request.path

    @property
    def app(self):
        """Return the app for which this view is configured."""
        if not self.app_id:
            raise ImproperlyConfigured('Missing attribute: app_id')

        return app_module.App.get(self.app_id)

    def get_form(self, *args, **kwargs):
        """Return an instance of this view's form.

        Also the form_class for this view to be None.

        """
        if not self.form_class:
            return None

        if not self.app.configure_when_disabled:
            status = self.get_common_status()
            if not status['is_enabled']:
                return None

        return super().get_form(*args, **kwargs)

    def get_common_status(self):
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
        initial = super().get_initial()
        initial.update(self.get_common_status())
        return initial

    def form_valid(self, form):
        """Enable/disable a service and set messages."""
        if not self.request._messages._queued_messages:
            messages.info(self.request, _('Setting unchanged'))

        return super().form_valid(form)

    def get_enable_disable_form(self):
        """Return an instance of the app enable/disable form.

        If the app can't be disabled by the user, return None.

        """
        if not self.app.can_be_disabled:
            return None

        initial = {'should_enable': not self.get_common_status()['is_enabled']}
        return forms.AppEnableDisableForm(initial=initial)

    def enable_disable_form_valid(self, form):
        """Form handling for enabling / disabling apps."""
        should_enable = form.cleaned_data['should_enable']
        if should_enable != self.app.is_enabled():
            if should_enable:
                self.app.enable()
            else:
                self.app.disable()

        return HttpResponseRedirect(self.request.path)

    def get_context_data(self, *args, **kwargs):
        """Add service to the context data."""
        context = super().get_context_data(*args, **kwargs)
        context.update(self.get_common_status())
        context['app_id'] = self.app.app_id
        context['is_running'] = app_is_running(self.app)
        context['app_info'] = self.app.info
        context['has_diagnostics'] = self.app.has_diagnostics()
        context['port_forwarding_info'] = get_port_forwarding_info(self.app)
        context['app_enable_disable_form'] = self.get_enable_disable_form()
        context['show_rerun_setup'] = True
        context['show_uninstall'] = not self.app.info.is_essential
        context['refresh_page_sec'] = None

        from plinth.modules.firewall.components import Firewall
        context['firewall'] = self.app.get_components_of_type(Firewall)

        context['has_backup_restore'] = _has_backup_restore(self.app)

        return context


class AppOperationsView(TemplateView):
    """View to show app page when some app operations are running."""
    app_id = None  # Set when app is instantiated.
    template_name = "app-operations.html"

    @property
    def app(self):
        """Return the app for which this view is configured."""
        if not self.app_id:
            raise ImproperlyConfigured('Missing attribute: app_id')

        return app_module.App.get(self.app_id)

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['app_id'] = self.app.app_id
        context['app_info'] = self.app.info
        context['operations'] = operation.manager.filter(self.app.app_id)
        context['refresh_page_sec'] = 0
        if context['operations']:
            context['refresh_page_sec'] = 3

        return context


class SetupView(TemplateView):
    """View to prompt and setup applications."""
    template_name = 'setup.html'

    def get_context_data(self, **kwargs):
        """Return the context data rendering the template."""
        context = super().get_context_data(**kwargs)
        app_id = self.kwargs['app_id']
        app = app_module.App.get(app_id)

        context['app_id'] = app.app_id
        context['app_info'] = app.info

        # Report any installed conflicting packages that will be removed.
        package_conflicts, package_conflicts_action = \
            self._get_app_package_conflicts(app)
        context['package_conflicts'] = package_conflicts
        context['package_conflicts_action'] = package_conflicts_action

        # Reuse the value of setup_state throughout the view for consistency.
        setup_state = app.get_setup_state()
        context['setup_state'] = setup_state
        context['operations'] = operation.manager.filter(app.app_id)
        context['show_rerun_setup'] = False
        context['show_uninstall'] = (not app.info.is_essential and setup_state
                                     != app_module.App.SetupState.NEEDS_SETUP)

        context['refresh_page_sec'] = None
        if context['setup_state'] == app_module.App.SetupState.UP_TO_DATE:
            context['refresh_page_sec'] = 0
        elif context['operations']:
            context['refresh_page_sec'] = 3

        return context

    def dispatch(self, request, *args, **kwargs):
        if request.method == 'POST':
            if 'install' in request.POST:
                # Handle installing/upgrading applications.
                # Start the application setup, and refresh the page every few
                # seconds to keep displaying the status.
                setup.run_setup_on_app(self.kwargs['app_id'])

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

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _get_app_package_conflicts(app_):
        """Return packages that may conflict with packages of an app."""
        components = app_.get_components_of_type(Packages)
        conflicts = []
        conflicts_action = None
        for component in components:
            component_conflicts = component.find_conflicts()
            if component_conflicts:
                conflicts += component_conflicts
                if conflicts_action in (None, Packages.ConflictsAction.IGNORE):
                    conflicts_action = component.conflicts_action

        return conflicts, conflicts_action


def is_available_view(request, app_id):
    """Return whether an app is available.

    This check may take quite some time, so don't perform this check when
    loading the app's setup page.
    """
    app = app_module.App.get(app_id)
    data = {'is_available': app.is_available()}
    return JsonResponse(data)


@require_POST
def rerun_setup_view(request, app_id):
    """Re-run setup on an app.

    This should be safe to perform on an already setup/running app. This may be
    useful in situations where the app is broken for unknown reason as notified
    by the diagnostics tests.
    """
    # Start the application setup, and refresh the page every few seconds to
    # keep displaying the status.
    setup.run_setup_on_app(app_id, rerun=True)

    # Give a moment for the setup process to start and show meaningful status.
    time.sleep(1)

    return redirect(reverse(f'{app_id}:index'))


class UninstallView(FormView):
    """View to uninstall apps."""

    form_class = forms.UninstallForm
    template_name = 'uninstall.html'

    def __init__(self, **kwargs):
        """Initialize extra instance members."""
        super().__init__(**kwargs)
        self.app = None

    def setup(self, request, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        super().setup(request, *args, **kwargs)
        app_id = self.kwargs['app_id']
        self.app = app_module.App.get(app_id)
        self.has_backup_restore = _has_backup_restore(self.app)

    def dispatch(self, request, *args, **kwargs):
        """Don't allow the view to be used on essential apps."""
        if self.app.info.is_essential:
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super().get_form_kwargs()
        kwargs['has_backup_restore'] = self.has_backup_restore
        return kwargs

    def get_context_data(self, *args, **kwargs):
        """Add app information to the context data."""
        context = super().get_context_data(*args, **kwargs)
        context['app_info'] = self.app.info
        return context

    def get_success_url(self):
        """Return the URL to redirect to after uninstall."""
        return reverse(self.kwargs['app_id'] + ':index')

    def form_valid(self, form):
        """Uninstall the app."""
        # Backup the app
        if self.has_backup_restore and form.cleaned_data['should_backup']:
            repository_id = form.cleaned_data['repository']

            import plinth.modules.backups.repository as repository_module
            repository = repository_module.get_instance(repository_id)
            if repository.flags.get('mountable'):
                repository.mount()

            name = repository.generate_archive_name() + ' ' + str(
                _('before uninstall of {app_id}')).format(
                    app_id=self.app.app_id)
            repository.create_archive(name, [self.app.app_id])

        # Uninstall
        setup.run_uninstall_on_app(self.app.app_id)

        return super().form_valid(form)


def notification_dismiss(request, id):
    """Dismiss a notification."""
    from .notification import Notification
    notes = Notification.list(key=id, user=request.user)
    if notes:
        # If a notification is not found, no need to dismiss it.
        notes[0].dismiss()

    return HttpResponseRedirect(_get_redirect_url_from_param(request))
