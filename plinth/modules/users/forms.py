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

import subprocess

from django import forms
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _, ugettext_lazy

from plinth import actions
from plinth.errors import ActionError
from plinth.modules import first_boot
from plinth.modules.security import set_restricted_access
from plinth.utils import is_user_admin
from plinth import module_loader

GROUP_CHOICES = (
    ('admin', _('admin')),
    ('wiki', _('wiki')),
)


class ValidNewUsernameCheckMixin(object):
    """Mixin to check if a username is valid for created new user."""

    def clean_username(self):
        """Check for username collisions with system users."""
        username = self.cleaned_data['username']
        if self.instance.username != username and \
                not self.is_valid_new_username():
            raise ValidationError(_('Username is taken or is reserved.'),
                                  code='invalid')

        return username

    def is_valid_new_username(self):
        """Check for username collisions with system users."""
        username = self.cleaned_data['username']
        try:
            subprocess.run(['getent', 'passwd', username],
                           stdout=subprocess.DEVNULL, check=True)
            # Exit code 0 means that the username is already in use.
            return False
        except subprocess.CalledProcessError:
            pass

        for module_name, module in module_loader.loaded_modules.items():
            for reserved_username in getattr(module, 'reserved_usernames', []):
                if username == reserved_username:
                    return False

        return True


class CreateUserForm(ValidNewUsernameCheckMixin, UserCreationForm):
    """Custom user create form.

    Include options to add user to groups.
    """

    groups = forms.MultipleChoiceField(
        choices=GROUP_CHOICES,
        label=ugettext_lazy('Groups'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=ugettext_lazy(
            'Select which services should be available to the new '
            'user. The user will be able to log in to services that '
            'support single sign-on through LDAP, if they are in the '
            'appropriate group.<br /><br />Users in the admin group '
            'will be able to log in to all services. They can also '
            'log in to the system through SSH and have '
            'administrative privileges (sudo).'))

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super(CreateUserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Save the user model and create LDAP user if required."""
        user = super(CreateUserForm, self).save(commit)

        if commit:
            try:
                actions.superuser_run(
                    'ldap',
                    ['create-user', user.get_username()],
                    input=self.cleaned_data['password1'].encode())
            except ActionError:
                messages.error(self.request,
                               _('Creating LDAP user failed.'))

            for group in self.cleaned_data['groups']:
                try:
                    actions.superuser_run(
                        'ldap',
                        ['add-user-to-group', user.get_username(), group])
                except ActionError:
                    messages.error(
                        self.request,
                        _('Failed to add new user to {group} group.')
                        .format(group=group))

                group_object, created = Group.objects.get_or_create(name=group)
                group_object.user_set.add(user)

        return user


class UserUpdateForm(ValidNewUsernameCheckMixin, forms.ModelForm):
    """When user info is changed, also updates LDAP user."""
    ssh_keys = forms.CharField(
        label=ugettext_lazy('SSH Keys'),
        required=False,
        widget=forms.Textarea,
        help_text=ugettext_lazy(
            'Setting an SSH public key will allow this user to '
            'securely log in to the system without using a '
            'password. You may enter multiple keys, one on each '
            'line. Blank lines and lines starting with # will be '
            'ignored.'))

    class Meta:
        """Metadata to control automatic form building."""
        fields = ('username', 'groups', 'ssh_keys', 'is_active')
        model = User
        widgets = {
            'groups': forms.widgets.CheckboxSelectMultiple(),
        }

    def __init__(self, request, username, *args, **kwargs):
        """Initialize the form with extra request argument."""
        for group, group_name in GROUP_CHOICES:
            Group.objects.get_or_create(name=group)

        self.request = request
        self.username = username

        super(UserUpdateForm, self).__init__(*args, **kwargs)

        if not is_user_admin(request):
            self.fields['is_active'].widget = forms.HiddenInput()
            self.fields['groups'].disabled = True

    def save(self, commit=True):
        """Update LDAP user name and groups after saving user model."""
        user = super(UserUpdateForm, self).save(commit)

        if commit:
            output = actions.superuser_run(
                'ldap', ['get-user-groups', self.username])
            old_groups = output.strip().split('\n')
            old_groups = [group for group in old_groups if group]

            if self.username != user.get_username():
                try:
                    actions.superuser_run(
                        'ldap',
                        ['rename-user', self.username, user.get_username()])
                except ActionError:
                    messages.error(self.request,
                                   _('Renaming LDAP user failed.'))

            new_groups = user.groups.values_list('name', flat=True)
            for old_group in old_groups:
                if old_group not in new_groups:
                    try:
                        actions.superuser_run(
                            'ldap',
                            ['remove-user-from-group', user.get_username(),
                             old_group])
                    except ActionError:
                        messages.error(self.request,
                                       _('Failed to remove user from group.'))

            for new_group in new_groups:
                if new_group not in old_groups:
                    try:
                        actions.superuser_run(
                            'ldap',
                            ['add-user-to-group', user.get_username(),
                             new_group])
                    except ActionError:
                        messages.error(self.request,
                                       _('Failed to add user to group.'))

            try:
                actions.superuser_run(
                    'ssh', ['set-keys', '--username', user.get_username(),
                            '--keys', self.cleaned_data['ssh_keys'].strip()])
            except ActionError:
                messages.error(self.request, _('Unable to set SSH keys.'))

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
                    'ldap',
                    ['set-user-password', user.get_username()],
                    input=self.cleaned_data['new_password1'].encode())
            except ActionError:
                messages.error(
                    self.request,
                    _('Changing LDAP user password failed.'))

        return user


class FirstBootForm(ValidNewUsernameCheckMixin, auth.forms.UserCreationForm):
    """User module first boot step: create a new admin user."""

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Create and log the user in."""
        user = super().save(commit=commit)
        if commit:
            first_boot.mark_step_done('users_firstboot')

            try:
                actions.superuser_run(
                    'ldap',
                    ['create-user', user.get_username()],
                    input=self.cleaned_data['password1'].encode())
            except ActionError:
                messages.error(self.request,
                               _('Creating LDAP user failed.'))

            try:
                actions.superuser_run(
                    'ldap',
                    ['add-user-to-group', user.get_username(), 'admin'])
            except ActionError:
                messages.error(self.request,
                               _('Failed to add new user to admin group.'))

            # Create initial Django groups
            for group_choice in GROUP_CHOICES:
                auth.models.Group.objects.get_or_create(name=group_choice[0])

            admin_group = auth.models.Group.objects.get(name='admin')
            admin_group.user_set.add(user)

            self.login_user(self.cleaned_data['username'],
                            self.cleaned_data['password1'])

            # Restrict console login to users in admin or sudo group
            try:
                set_restricted_access(True)
            except Exception:
                messages.error(self.request,
                               _('Failed to restrict console access.'))

        return user

    def login_user(self, username, password):
        """Try to login the user with the credentials provided"""
        try:
            user = auth.authenticate(username=username, password=password)
            auth.login(self.request, user)
        except Exception:
            pass
        else:
            message = _('User account created, you are now logged in')
            messages.success(self.request, message)
