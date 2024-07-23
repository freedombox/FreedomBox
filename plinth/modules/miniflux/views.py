# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Miniflux."""

import logging

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView

from plinth import views

from . import privileged
from .forms import UserCredentialsForm

logger = logging.getLogger(__name__)


class MinifluxAppView(views.AppView):
    """Serve configuration page."""

    app_id = 'miniflux'
    template_name = 'miniflux.html'


class CreateAdminUserView(SuccessMessageMixin, FormView):
    """View to create a new admin user."""

    form_class = UserCredentialsForm
    prefix = 'miniflux'
    template_name = 'form.html'
    success_url = reverse_lazy('miniflux:index')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Admin User')
        return context

    def form_valid(self, form):
        """Create the admin user on valid form submission."""
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            privileged.create_admin_user(username, password)
            self.success_message = _('Created admin user: {username}').format(
                username=username)
        except Exception as error:
            messages.error(
                self.request,
                _('An error occurred while creating the user: {error}.').
                format(error=error))

        return super().form_valid(form)


class ResetUserPasswordView(SuccessMessageMixin, FormView):
    """View to reset a user password."""

    form_class = UserCredentialsForm
    prefix = 'miniflux'
    template_name = 'form.html'
    success_url = reverse_lazy('miniflux:index')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Reset User Password')
        return context

    def form_valid(self, form):
        """Reset password on valid form submission."""
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']

        try:
            privileged.reset_user_password(username, password)
            self.success_message = _('Password reset for user: {username}'
                                     ).format(username=username)
        except Exception as error:
            messages.error(
                self.request,
                _('An error occurred during password reset: {error}.').format(
                    error=str(error).strip()))

        return super().form_valid(form)
