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
    """Custom user create form.

    Include option to also create LDAP user.
    """

    add_ldap_user = forms.BooleanField(
        label=_('Also create an LDAP user'),
        required=False,
        help_text=_('This will allow the new user to log in to various '
                    'services that support single sign-on through LDAP.'))

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super(CreateUserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Save the user model and create LDAP user if required."""
        user = super(CreateUserForm, self).save(commit)

        if commit:
            if self.cleaned_data['add_ldap_user']:
                try:
                    actions.superuser_run(
                        'create-ldap-user',
                        [user.get_username(), self.cleaned_data['password1']])
                except ActionError:
                    messages.error(self.request,
                                   _('Creating LDAP user failed.'))

        return user


class UserUpdateForm(forms.ModelForm):
    """When user info is changed, also updates LDAP user."""

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
        """Update LDAP user name after saving user model."""
        user = super(UserUpdateForm, self).save(commit)

        if commit:
            if self.username != user.get_username():
                try:
                    actions.superuser_run('rename-ldap-user',
                                          [self.username, user.get_username()])
                except ActionError:
                    messages.error(self.request,
                                   _('Renaming LDAP user failed.'))

        return user


class UserChangePasswordForm(SetPasswordForm):
    """Custom form that also updates password for LDAP users."""

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super(UserChangePasswordForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Save the user model and change LDAP password as well."""
        user = super(UserChangePasswordForm, self).save(commit)
        if commit:
            try:
                actions.superuser_run(
                    'change-ldap-user-password',
                    [user.get_username(), self.cleaned_data['new_password1']])
            except ActionError:
                messages.error(
                    self.request,
                    _('Changing LDAP user password failed.'))

        return user
