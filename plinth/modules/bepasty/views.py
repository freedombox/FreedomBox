# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the bepasty app.
"""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from plinth.errors import ActionError
from plinth.modules import bepasty
from plinth.views import AppView

from .forms import AddPasswordForm, SetDefaultPermissionsForm


class BepastyView(AppView):
    """Serve configuration page."""
    app_id = 'bepasty'
    form_class = SetDefaultPermissionsForm
    template_name = 'bepasty.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['passwords'] = bepasty.list_passwords()
        return context

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        initial = super().get_initial()
        initial['default_permissions'] = bepasty.get_default_permissions()
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_data = form.initial
        form_data = form.cleaned_data

        if old_data['default_permissions'] != form_data['default_permissions']:
            try:
                bepasty.set_default_permissions(
                    form_data['default_permissions'])
                messages.success(self.request, _('Configuration updated.'))
            except ActionError:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        return super().form_valid(form)


class AddPasswordView(SuccessMessageMixin, FormView):
    """View to add a new password."""
    form_class = AddPasswordForm
    prefix = 'bepasty'
    template_name = 'bepasty_add.html'
    success_url = reverse_lazy('bepasty:index')
    success_message = _('Password added.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Password')
        return context

    def form_valid(self, form):
        """Add the password on valid form submission."""
        _add_password(form.cleaned_data)
        return super().form_valid(form)


def _add_password(form_data):
    bepasty.add_password(form_data['permissions'], form_data['comment'])


@require_POST
def remove(request, password):
    """View to remove a password."""
    bepasty.remove_password(password)
    messages.success(request, _('Password deleted.'))
    return redirect(reverse_lazy('bepasty:index'))
