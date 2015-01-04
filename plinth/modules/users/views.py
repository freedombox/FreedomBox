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

from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.edit import (CreateView, DeleteView, UpdateView,
                                       FormView)
from django.views.generic import ListView
from gettext import gettext as _


subsubmenu = [{'url': reverse_lazy('users:index'),
               'text': _('Users')},
              {'url': reverse_lazy('users:create'),
               'text': _('Create User')}]


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
    form_class = UserCreationForm
    template_name = 'users_create.html'
    model = User
    success_message = _('User %(username)s created.')
    success_url = reverse_lazy('users:create')
    title = _('Create User')


class UserList(ContextMixin, ListView):
    """View to list users."""
    model = User
    template_name = 'users_list.html'
    title = _('Users')


class UserUpdate(ContextMixin, SuccessMessageMixin, UpdateView):
    """View to update a user's details."""
    template_name = 'users_update.html'
    fields = ('username', 'groups', 'is_active')
    model = User
    slug_field = 'username'
    success_message = _('User %(username)s updated.')
    title = _('Edit User')
    widgets = {
        'groups': forms.widgets.CheckboxSelectMultiple(),
    }

    def get_form_class(self):
        """Return a form class generated from user model."""
        return forms.models.modelform_factory(self.model, fields=self.fields,
                                              widgets=self.widgets)

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
    title = _('Delete User')

    def delete(self, *args, **kwargs):
        """Set the success message of deleting the user.

        The SuccessMessageMixin doesn't work with the DeleteView on Django1.7,
        so set the success message manually here.
        """
        message = _('User %s deleted.') % self.kwargs['slug']
        output = super(UserDelete, self).delete(*args, **kwargs)
        messages.success(self.request, message)
        return output


class UserChangePassword(ContextMixin, SuccessMessageMixin, FormView):
    """View to change user password."""
    template_name = 'users_change_password.html'
    form_class = SetPasswordForm
    title = _('Change Password')
    success_message = _('Password changed successfully.')

    def get_form_kwargs(self):
        """Make the user object available to the form"""
        kwargs = super(UserChangePassword, self).get_form_kwargs()
        kwargs['user'] = User.objects.get(username=self.kwargs['slug'])
        return kwargs

    def get_success_url(self):
        return reverse('users:edit', kwargs={'slug': self.kwargs['slug']})

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        return super(UserChangePassword, self).form_valid(form)
