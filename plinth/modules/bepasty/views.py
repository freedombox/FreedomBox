# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the bepasty app."""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from plinth.views import AppView

from . import privileged
from .forms import AddPasswordForm, SetDefaultPermissionsForm

# i18n for permission comments
PERMISSION_COMMENTS_STRINGS = {
    'admin': _('admin'),
    'editor': _('editor'),
    'viewer': _('viewer'),
}


class BepastyView(AppView):
    """Serve configuration page."""

    app_id = 'bepasty'
    form_class = SetDefaultPermissionsForm
    template_name = 'bepasty.html'

    def __init__(self, *args, **kwargs):
        """Initialize the view."""
        super().__init__(*args, **kwargs)
        self.conf = None

    def _get_configuration(self):
        """Return the current configuration."""
        if not self.conf:
            self.conf = privileged.get_configuration()

        return self.conf

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        permissions_short_text = {
            'read': _('Read'),
            'create': _('Create'),
            'list': _('List'),
            'delete': _('Delete'),
            'admin': _('Admin')
        }
        context = super().get_context_data(**kwargs)
        conf = self._get_configuration()
        passwords = []
        for password, permissions in conf['PERMISSIONS'].items():
            permissions = permissions.split(',')
            permissions = [
                str(permissions_short_text[permission])
                for permission in permissions if permission
            ]
            passwords.append({
                'password': password,
                'permissions': ', '.join(permissions),
                'comment': conf['PERMISSION_COMMENTS'].get(password) or ''
            })
        context['passwords'] = passwords
        return context

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        initial = super().get_initial()
        default = self._get_configuration().get('DEFAULT_PERMISSIONS', '')
        default = ' '.join(default.split(','))
        default = 'read list' if default == 'list read' else default
        initial['default_permissions'] = default
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_data = form.initial
        form_data = form.cleaned_data

        if old_data['default_permissions'] != form_data['default_permissions']:
            try:
                privileged.set_default(
                    form_data['default_permissions'].split(' '))
                messages.success(self.request, _('Configuration updated.'))
            except Exception:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        return super().form_valid(form)


class AddPasswordView(SuccessMessageMixin, FormView):
    """View to add a new password."""

    form_class = AddPasswordForm
    prefix = 'bepasty'
    template_name = 'form.html'
    success_url = reverse_lazy('bepasty:index')
    success_message = _('Password added.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Password')
        return context

    def form_valid(self, form):
        """Add the password on valid form submission."""
        form_data = form.cleaned_data
        privileged.add_password(form_data['permissions'], form_data['comment'])
        return super().form_valid(form)


@require_POST
def remove(request, password):
    """View to remove a password."""
    privileged.remove_password(password)
    messages.success(request, _('Password deleted.'))
    return redirect(reverse_lazy('bepasty:index'))
