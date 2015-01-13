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
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from gettext import gettext as _

from plinth import actions


class CreateUserForm(UserCreationForm):
    """Custom user create form with option to also create POSIX user."""

    add_posix_user = forms.BooleanField(
        label=_('Also create POSIX user'),
        required=False,
        help_text=_('This will allow the new user to log in to the system '
                    'through SSH. The new user will also have administrative '
                    'privileges (sudo).'))

    def save(self, commit=True):
        user = super(CreateUserForm, self).save(commit)
        if commit and self.cleaned_data['add_posix_user']:
            actions.superuser_run(
                'create-user',
                [user.username, self.cleaned_data['password1']])
        return user


class UserUpdateForm(forms.ModelForm):
    """When user is enabled/disabled, also enables/disables the POSIX user."""

    class Meta:
        fields = ('username', 'groups', 'is_active')
        model = User
        widgets = {
            'groups': forms.widgets.CheckboxSelectMultiple(),
        }

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit)
        if commit:
            if user.is_active:
                actions.superuser_run('enable-user', [user.username])
            else:
                actions.superuser_run('disable-user', [user.username])
        return user


class UserChangePasswordForm(SetPasswordForm):
    """Custom form that also updates password for POSIX users."""

    def save(self, commit=True):
        user = super(UserChangePasswordForm, self).save(commit)
        if commit:
            actions.superuser_run(
                'change-user-password',
                [user.username, self.cleaned_data['new_password1']])
        return user
