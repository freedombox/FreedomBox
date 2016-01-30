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

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.edit import (CreateView, DeleteView, UpdateView,
                                       FormView)
from django.views.generic import ListView
from django.utils.translation import ugettext as _, ugettext_lazy

from .forms import CreateUserForm, UserChangePasswordForm, UserUpdateForm
from plinth import actions
from plinth.errors import ActionError


subsubmenu = [{'url': reverse_lazy('users:index'),
               'text': ugettext_lazy('Users')},
              {'url': reverse_lazy('users:create'),
               'text': ugettext_lazy('Create User')}]


class ContextMixin(object):
    """Mixin to add 'subsubmenu' and 'title' to the context."""
    def get_context_data(self, **kwargs):
        """Use self.title and the module-level subsubmenu"""
        context = super(ContextMixin, self).get_context_data(**kwargs)
        context['subsubmenu'] = subsubmenu
        context['title'] = getattr(self, 'title', '')
        return context


class UserCreate(ContextMixin, SuccessMessageMixin, CreateView):
    """View to create a new user."""
    form_class = CreateUserForm
    template_name = 'users_create.html'
    model = User
    success_message = ugettext_lazy('User %(username)s created.')
    success_url = reverse_lazy('users:create')
    title = ugettext_lazy('Create User')

    def get_form_kwargs(self):
        """Make the request object available to the form."""
        kwargs = super(UserCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class UserList(ContextMixin, ListView):
    """View to list users."""
    model = User
    template_name = 'users_list.html'
    title = ugettext_lazy('Users')


class UserUpdate(ContextMixin, SuccessMessageMixin, UpdateView):
    """View to update a user's details."""
    template_name = 'users_update.html'
    model = User
    form_class = UserUpdateForm
    slug_field = 'username'
    success_message = ugettext_lazy('User %(username)s updated.')
    title = ugettext_lazy('Edit User')

    def get_form_kwargs(self):
        """Make the requst object available to the form."""
        kwargs = super(UserUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['username'] = self.object.username
        return kwargs

    def get_initial(self):
        """Return the data for initial form load."""
        initial = super(UserUpdate, self).get_initial()
        initial['ssh_keys'] = actions.superuser_run(
            'ssh', ['get-keys', '--username', self.object.username]).strip()
        return initial

    def get_success_url(self):
        """Return the URL to redirect to in case of successful updation."""
        return reverse('users:edit', kwargs={'slug': self.object.username})


class UserDelete(ContextMixin, DeleteView):
    """Handle deleting users, showing a confirmation dialog first.

    On GET, display a confirmation page.
    On POST, delete the user.
    """
    template_name = 'users_delete.html'
    model = User
    slug_field = 'username'
    success_url = reverse_lazy('users:index')
    title = ugettext_lazy('Delete User')

    def delete(self, *args, **kwargs):
        """Set the success message of deleting the user.

        The SuccessMessageMixin doesn't work with the DeleteView on Django1.7,
        so set the success message manually here.
        """
        output = super(UserDelete, self).delete(*args, **kwargs)

        message = _('User {user} deleted.').format(user=self.kwargs['slug'])
        messages.success(self.request, message)

        try:
            actions.superuser_run('ldap', ['delete-user', self.kwargs['slug']])
        except ActionError:
            messages.error(self.request,
                           _('Deleting LDAP user failed.'))

        return output


class UserChangePassword(ContextMixin, SuccessMessageMixin, FormView):
    """View to change user password."""
    template_name = 'users_change_password.html'
    form_class = UserChangePasswordForm
    title = ugettext_lazy('Change Password')
    success_message = ugettext_lazy('Password changed successfully.')

    def get_form_kwargs(self):
        """Make the user object available to the form."""
        kwargs = super(UserChangePassword, self).get_form_kwargs()
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
        return super(UserChangePassword, self).form_valid(form)
