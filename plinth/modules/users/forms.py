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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from gettext import gettext as _

from plinth import actions
from plinth.errors import ActionError


class CreateUserForm(UserCreationForm):
    """Custom user create form with option to also create POSIX user."""

    add_posix_user = forms.BooleanField(
        label=_('Also create a POSIX system user'),
        required=False,
        help_text=_('This will allow the new user to log in to the system '
                    'through SSH. The new user will also have administrative '
                    'privileges (sudo).'))

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super(CreateUserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Save the user model and create POSIX user if required."""
        user = super(CreateUserForm, self).save(commit)
        if commit and self.cleaned_data['add_posix_user']:
            try:
                actions.superuser_run(
                    'create-user',
                    [user.get_username(), self.cleaned_data['password1']])
            except ActionError:
                messages.error(self.request,
                               _('Creating POSIX system user failed.'))

        return user


class UserUpdateForm(forms.ModelForm):
    """When user is enabled/disabled, also enables/disables the POSIX user."""

    class Meta:
        """Metadata to control automatic form building."""
        fields = ('username', 'groups', 'is_active')
        model = User
        widgets = {
            'groups': forms.widgets.CheckboxSelectMultiple(),
        }

    def __init__(self, request, username, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        self.username = username
        super(UserUpdateForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Enable/disable POSIX user after saving user model."""
        user = super(UserUpdateForm, self).save(commit)

        if commit:
            try:
                if user.is_active:
                    actions.superuser_run('enable-user', [user.get_username()])
                else:
                    actions.superuser_run('disable-user',
                                          [user.get_username()])
            except ActionError:
                messages.error(
                    self.request,
                    _('Setting active status for POSIX system user failed.'))

            try:
                if self.username != user.get_username():
                    actions.superuser_run('rename-user',
                                          [self.username, user.get_username()])
            except ActionError:
                messages.error(self.request,
                               _('Renaming POSIX system user failed.'))

        return user


class UserChangePasswordForm(SetPasswordForm):
    """Custom form that also updates password for POSIX users."""

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super(UserChangePasswordForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Save the user model and change POSIX password as well."""
        user = super(UserChangePasswordForm, self).save(commit)
        if commit:
            try:
                actions.superuser_run(
                    'change-user-password',
                    [user.get_username(), self.cleaned_data['new_password1']])
            except ActionError:
                messages.error(
                    self.request,
                    _('Changing POSIX system user password failed.'))

        return user
