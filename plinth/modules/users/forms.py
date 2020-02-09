#
# This file is part of FreedomBox.
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

import pwd
import re

import plinth.forms
from django import forms
from django.contrib import auth, messages
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group, User
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from plinth import actions, module_loader
from plinth.errors import ActionError
from plinth.modules import first_boot, users
from plinth.modules.security import set_restricted_access
from plinth.translation import set_language
from plinth.utils import is_user_admin

from . import get_last_admin_user


def get_group_choices():
    """Return localized group description and group name in one string."""
    admin_group = ('admin', _('Access to all services and system settings'))
    users.register_group(admin_group)
    choices = [(k, ('{} ({})'.format(users.groups[k], k)))
               for k in users.groups]
    return sorted(choices, key=lambda g: g[0])


class ValidNewUsernameCheckMixin(object):
    """Mixin to check if a username is valid for created new user."""

    def clean_username(self):
        """Check for username collisions with system users."""
        username = self.cleaned_data['username']
        if self.instance.username != username and \
                not self.is_valid_new_username():
            raise ValidationError(
                _('Username is taken or is reserved.'), code='invalid')

        return username

    def is_valid_new_username(self):
        """Check for username collisions with system users."""
        username = self.cleaned_data['username']
        existing_users = (a.pw_name.lower() for a in pwd.getpwall())
        if username.lower() in existing_users:
            return False

        for module_name, module in module_loader.loaded_modules.items():
            for reserved_username in getattr(module, 'reserved_usernames', []):
                if username.lower() == reserved_username.lower():
                    return False

        return True


@deconstructible
class UsernameValidator(validators.RegexValidator):
    """Username validator.

    Compared to django builtin ASCIIUsernameValidator, do not allow
    '+' characters and no '-' character at the beginning.

    """
    regex = r'^[\w.@][\w.@-]+\Z'
    message = ugettext_lazy('Enter a valid username.')
    flags = re.ASCII


USERNAME_FIELD = forms.CharField(
    max_length=150, validators=[UsernameValidator()],
    help_text=ugettext_lazy('Required. 150 characters or fewer. English '
                            'letters, digits and @/./-/_ only.'))


class CreateUserForm(ValidNewUsernameCheckMixin,
                     plinth.forms.LanguageSelectionFormMixin,
                     UserCreationForm):
    """Custom user create form.

    Include options to add user to groups.
    """
    username = USERNAME_FIELD
    groups = forms.MultipleChoiceField(
        choices=get_group_choices(), label=ugettext_lazy('Permissions'),
        required=False, widget=forms.CheckboxSelectMultiple,
        help_text=ugettext_lazy(
            'Select which services should be available to the new '
            'user. The user will be able to log in to services that '
            'support single sign-on through LDAP, if they are in the '
            'appropriate group.<br /><br />Users in the admin group '
            'will be able to log in to all services. They can also '
            'log in to the system through SSH and have '
            'administrative privileges (sudo).'))

    language = plinth.forms.LanguageSelectionFormMixin.language

    class Meta(UserCreationForm.Meta):
        """Metadata to control automatic form building."""
        fields = ('username', 'password1', 'password2', 'groups', 'language')

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super(CreateUserForm, self).__init__(*args, **kwargs)
        self.fields['groups'].choices = get_group_choices()
        self.fields['username'].widget.attrs.update({
            'autofocus': 'autofocus',
            'autocapitalize': 'none',
            'autocomplete': 'username'
        })

    def save(self, commit=True):
        """Save the user model and create LDAP user if required."""
        user = super(CreateUserForm, self).save(commit)

        if commit:
            user.userprofile.language = self.cleaned_data['language']
            user.userprofile.save()

            try:
                actions.superuser_run(
                    'users',
                    ['create-user', user.get_username()],
                    input=self.cleaned_data['password1'].encode())
            except ActionError:
                messages.error(self.request, _('Creating LDAP user failed.'))

            for group in self.cleaned_data['groups']:
                try:
                    actions.superuser_run(
                        'users',
                        ['add-user-to-group',
                         user.get_username(), group])
                except ActionError:
                    messages.error(
                        self.request,
                        _('Failed to add new user to {group} group.').format(
                            group=group))

                group_object, created = Group.objects.get_or_create(name=group)
                group_object.user_set.add(user)

        return user


class UserUpdateForm(ValidNewUsernameCheckMixin,
                     plinth.forms.LanguageSelectionFormMixin, forms.ModelForm):
    """When user info is changed, also updates LDAP user."""
    username = USERNAME_FIELD
    ssh_keys = forms.CharField(
        label=ugettext_lazy('Authorized SSH Keys'), required=False,
        widget=forms.Textarea, help_text=ugettext_lazy(
            'Setting an SSH public key will allow this user to '
            'securely log in to the system without using a '
            'password. You may enter multiple keys, one on each '
            'line. Blank lines and lines starting with # will be '
            'ignored.'))

    language = plinth.forms.LanguageSelectionFormMixin.language

    class Meta:
        """Metadata to control automatic form building."""
        fields = ('username', 'groups', 'ssh_keys', 'language', 'is_active')
        model = User
        widgets = {
            'groups': plinth.forms.CheckboxSelectMultipleWithReadOnly(),
        }

    def __init__(self, request, username, *args, **kwargs):
        """Initialize the form with extra request argument."""
        group_choices = dict(get_group_choices())
        for group in group_choices:
            Group.objects.get_or_create(name=group)

        self.request = request
        self.username = username
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.is_last_admin_user = get_last_admin_user() == self.username
        self.fields['username'].widget.attrs.update({
            'autofocus': 'autofocus',
            'autocapitalize': 'none',
            'autocomplete': 'username'
        })

        choices = []

        for c in sorted(self.fields['groups'].choices, key=lambda x: x[1]):
            # Handle case where groups exist in database for
            # applications not installed yet.
            if c[1] in group_choices:
                # Replace group names with descriptions
                if c[1] == 'admin' and self.is_last_admin_user:
                    choices.append((c[0], {
                        'label': group_choices[c[1]],
                        'readonly': True
                    }))
                else:
                    choices.append((c[0], group_choices[c[1]]))

        self.fields['groups'].label = _('Permissions')
        self.fields['groups'].choices = choices

        if not is_user_admin(request):
            self.fields['is_active'].widget = forms.HiddenInput()
            self.fields['groups'].disabled = True

        if self.is_last_admin_user:
            self.fields['is_active'].disabled = True

    def save(self, commit=True):
        """Update LDAP user name and groups after saving user model."""
        user = super(UserUpdateForm, self).save(commit=False)
        # Profile is auto saved with user object
        user.userprofile.language = self.cleaned_data['language']

        # If user is updating their own profile then only translate the pages
        if self.username == self.request.user.username:
            set_language(self.request, None, user.userprofile.language)

        if commit:
            user.save()
            self.save_m2m()

            output = actions.superuser_run('users',
                                           ['get-user-groups', self.username])
            old_groups = output.strip().split('\n')
            old_groups = [group for group in old_groups if group]

            if self.username != user.get_username():
                try:
                    actions.superuser_run(
                        'users',
                        ['rename-user', self.username,
                         user.get_username()])
                except ActionError:
                    messages.error(self.request,
                                   _('Renaming LDAP user failed.'))

            new_groups = user.groups.values_list('name', flat=True)
            for old_group in old_groups:
                if old_group not in new_groups:
                    try:
                        actions.superuser_run('users', [
                            'remove-user-from-group',
                            user.get_username(), old_group
                        ])
                    except ActionError:
                        messages.error(self.request,
                                       _('Failed to remove user from group.'))

            for new_group in new_groups:
                if new_group not in old_groups:
                    try:
                        actions.superuser_run('users', [
                            'add-user-to-group',
                            user.get_username(), new_group
                        ])
                    except ActionError:
                        messages.error(self.request,
                                       _('Failed to add user to group.'))

            try:
                actions.superuser_run('ssh', [
                    'set-keys', '--username',
                    user.get_username(), '--keys',
                    self.cleaned_data['ssh_keys'].strip()
                ])
            except ActionError:
                messages.error(self.request, _('Unable to set SSH keys.'))

            is_active = self.cleaned_data['is_active']
            if self.initial['is_active'] != is_active:
                if is_active:
                    status = 'active'
                else:
                    status = 'inactive'
                try:
                    actions.superuser_run(
                        'users',
                        ['set-user-status',
                         user.get_username(), status])
                except ActionError:
                    messages.error(self.request,
                                   _('Failed to change user status.'))

        return user

    def validate_last_admin_user(self, groups):
        group_names = [group.name for group in groups]
        if 'admin' not in group_names:
            raise ValidationError(
                _('Cannot delete the only administrator in the system.'))

    def clean(self):
        """Override clean to add form validation logic."""
        cleaned_data = super().clean()
        if self.is_last_admin_user:
            self.validate_last_admin_user(cleaned_data.get("groups"))
        return cleaned_data


class UserChangePasswordForm(SetPasswordForm):
    """Custom form that also updates password for LDAP users."""

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super(UserChangePasswordForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'autofocus': 'autofocus'
        })

    def save(self, commit=True):
        """Save the user model and change LDAP password as well."""
        user = super(UserChangePasswordForm, self).save(commit)
        if commit:
            try:
                actions.superuser_run(
                    'users', ['set-user-password',
                              user.get_username()],
                    input=self.cleaned_data['new_password1'].encode())
            except ActionError:
                messages.error(self.request,
                               _('Changing LDAP user password failed.'))

        return user


class FirstBootForm(ValidNewUsernameCheckMixin, auth.forms.UserCreationForm):
    """User module first boot step: create a new admin user."""
    username = USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autofocus': 'autofocus'})

    def save(self, commit=True):
        """Create and log the user in."""
        user = super().save(commit=commit)
        if commit:
            first_boot.mark_step_done('users_firstboot')

            try:
                actions.superuser_run(
                    'users',
                    ['create-user', user.get_username()],
                    input=self.cleaned_data['password1'].encode())
            except ActionError:
                messages.error(self.request, _('Creating LDAP user failed.'))

            try:
                actions.superuser_run(
                    'users',
                    ['add-user-to-group',
                     user.get_username(), 'admin'])
            except ActionError:
                messages.error(self.request,
                               _('Failed to add new user to admin group.'))

            # Create initial Django groups
            for group_choice in get_group_choices():
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
