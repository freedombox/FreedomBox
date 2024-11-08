# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for user app."""

import django.views.generic
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy
from django.views.generic.edit import (CreateView, FormView, UpdateView)

import plinth.modules.ssh.privileged as ssh_privileged
from plinth import translation
from plinth.modules import first_boot
from plinth.utils import is_user_admin
from plinth.views import AppView

from . import privileged
from .forms import (CreateUserForm, FirstBootForm, UserChangePasswordForm,
                    UserUpdateForm)


class ContextMixin:
    """Mixin to add 'title' to the template context."""

    def get_context_data(self, **kwargs):
        """Add self.title to template context."""
        context = super().get_context_data(**kwargs)
        context['title'] = getattr(self, 'title', '')
        return context


class UserCreate(ContextMixin, SuccessMessageMixin, CreateView):
    """View to create a new user."""

    form_class = CreateUserForm
    template_name = 'users_create.html'
    model = User
    success_message = gettext_lazy('User %(username)s created.')
    success_url = reverse_lazy('users:create')
    title = gettext_lazy('Create User')

    def get_form_kwargs(self):
        """Make the request object available to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        """Return the URL to redirect to in case of successful updation."""
        return reverse('users:index')


class UserList(AppView, ContextMixin, django.views.generic.ListView):
    """View to list users."""

    model = User
    template_name = 'users_list.html'
    title = gettext_lazy('Users')
    app_id = 'users'


class UserUpdate(ContextMixin, SuccessMessageMixin, UpdateView):
    """View to update a user's details."""

    template_name = 'users_update.html'
    model = User
    form_class = UserUpdateForm
    slug_field = 'username'
    success_message = gettext_lazy('User %(username)s updated.')
    title = gettext_lazy('Edit User')

    def dispatch(self, request, *args, **kwargs):
        """Handle a request and return a HTTP response."""
        if self.request.user.get_username() != self.kwargs['slug'] \
                and not is_user_admin(self.request):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Make the request object available to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['username'] = self.object.username
        return kwargs

    def get_initial(self):
        """Return the data for initial form load."""
        initial = super().get_initial()
        try:
            ssh_keys = ssh_privileged.get_keys(self.object.username)
            initial['ssh_keys'] = ssh_keys.strip()
            initial['language'] = self.object.userprofile.language
        except Exception:
            pass

        return initial

    def get_success_url(self):
        """Return the URL to redirect to in case of successful updation."""
        return reverse('users:edit', kwargs={'slug': self.object.username})

    def form_valid(self, form):
        """Set the user language if necessary."""

        is_user_deleted = form.cleaned_data.get('delete')
        if is_user_deleted:
            self.success_message = gettext_lazy('User %(username)s deleted.')
        response = super().form_valid(form)
        if is_user_deleted:
            return HttpResponseRedirect(reverse_lazy('users:index'))

        # If user is updating their own profile then set the language for
        # current session too.
        if self.object.username == self.request.user.username:
            translation.set_language(self.request, response,
                                     self.request.user.userprofile.language)

        return response


class UserChangePassword(ContextMixin, SuccessMessageMixin, FormView):
    """View to change user password."""

    template_name = 'users_change_password.html'
    form_class = UserChangePasswordForm
    title = gettext_lazy('Change Password')
    success_message = gettext_lazy('Password changed successfully.')

    def dispatch(self, request, *args, **kwargs):
        """Handle a request and return a HTTP response."""
        if self.request.user.get_username() != self.kwargs['slug'] \
                and not is_user_admin(self.request):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Make the user object available to the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['user'] = User.objects.get(username=self.kwargs['slug'])
        return kwargs

    def get_success_url(self):
        """Return the URL to go to on successful sumbission."""
        return reverse('users:edit', kwargs={'slug': self.kwargs['slug']})

    def form_valid(self, form):
        """Save the form if the submission is valid.

        Django user session authentication hashes are based on password to have
        the ability to logout all sessions on password change.  Update the
        session authentications to ensure that the current sessions is not
        logged out.
        """
        form.save()
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)


class FirstBootView(django.views.generic.CreateView):
    """Create user account and log the user in."""

    template_name = 'users_firstboot.html'
    form_class = FirstBootForm

    def dispatch(self, request, *args, **kwargs):
        """Check if there is no possibility to create a new admin account."""
        if request.method == 'POST' and 'skip' in request.POST:
            first_boot.mark_step_done('users_firstboot')
            return HttpResponseRedirect(reverse(first_boot.next_step()))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add admin users to context data."""
        context = super().get_context_data(*args, **kwargs)
        context['admin_users'] = privileged.get_group_users('admin')
        return context

    def get_form_kwargs(self):
        """Make request available to the form (to insert messages)."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        """Return the next first boot step after valid form submission."""
        return reverse(first_boot.next_step())
