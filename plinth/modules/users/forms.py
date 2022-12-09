# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django forms for user management."""

import pwd
import re

from django import forms
from django.contrib import auth, messages
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group, User
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

import plinth.forms
import plinth.modules.ssh.privileged as ssh_privileged
from plinth.modules import first_boot
from plinth.utils import is_user_admin

from . import get_last_admin_user, privileged
from .components import UsersAndGroups


class ValidNewUsernameCheckMixin:
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
        existing_users = (a.pw_name.lower() for a in pwd.getpwall())
        if username.lower() in existing_users:
            return False

        if UsersAndGroups.is_username_reserved(username.lower()):
            return False

        return True


@deconstructible
class UsernameValidator(validators.RegexValidator):
    """Username validator.

    Compared to django builtin ASCIIUsernameValidator, do not allow
    '+' characters and no '-' character at the beginning.

    """
    regex = r'^[\w.@][\w.@-]+\Z'
    message = gettext_lazy('Enter a valid username.')
    flags = re.ASCII


USERNAME_FIELD = forms.CharField(
    label=gettext_lazy('Username'), max_length=150,
    validators=[UsernameValidator()],
    help_text=gettext_lazy('Required. 150 characters or fewer. English '
                           'letters, digits and @/./-/_ only.'))


class PasswordConfirmForm(forms.Form):
    """Password confirmation form."""

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label=gettext_lazy('Authorization Password'))

    def __init__(self, *args, **kwargs):
        """Initialize form."""
        super().__init__(*args, **kwargs)

        self.fields['confirm_password'].help_text = _(
            'Enter the password for user "{user}" to authorize account '
            'modifications.').format(user=self.request.user.username)

    def clean_confirm_password(self):
        """Check that current user's password matches."""
        confirm_password = self.cleaned_data['confirm_password']
        password_matches = check_password(confirm_password,
                                          self.request.user.password)
        if not password_matches:
            raise ValidationError(_('Invalid password.'), code='invalid')

        return confirm_password


class CreateUserForm(ValidNewUsernameCheckMixin,
                     plinth.forms.LanguageSelectionFormMixin,
                     PasswordConfirmForm, UserCreationForm):
    """Custom user create form.

    Include options to add user to groups.
    """

    username = USERNAME_FIELD
    groups = forms.MultipleChoiceField(
        choices=UsersAndGroups.get_group_choices,
        label=gettext_lazy('Permissions'), required=False,
        widget=plinth.forms.CheckboxSelectMultiple, help_text=gettext_lazy(
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

        fields = ('username', 'password1', 'password2', 'groups', 'language',
                  'confirm_password')

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'autofocus': 'autofocus',
            'autocapitalize': 'none',
            'autocomplete': 'username',
        })

    def save(self, commit=True):
        """Save the user model and create LDAP user if required."""
        user = super().save(commit)

        if commit:
            user.userprofile.language = self.cleaned_data['language']
            user.userprofile.save()
            auth_username = self.request.user.username
            confirm_password = self.cleaned_data['confirm_password']

            try:
                privileged.create_user(user.get_username(),
                                       self.cleaned_data['password1'],
                                       auth_username, confirm_password)
            except Exception as error:
                messages.error(
                    self.request,
                    _('Creating LDAP user failed: {error}'.format(
                        error=error)))

            for group in self.cleaned_data['groups']:
                try:
                    privileged.add_user_to_group(user.get_username(), group,
                                                 auth_username,
                                                 confirm_password)
                except Exception as error:
                    messages.error(
                        self.request,
                        _('Failed to add new user to {group} group: {error}').
                        format(group=group, error=error))

                group_object, created = Group.objects.get_or_create(name=group)
                group_object.user_set.add(user)

        return user


class UserUpdateForm(ValidNewUsernameCheckMixin, PasswordConfirmForm,
                     plinth.forms.LanguageSelectionFormMixin, forms.ModelForm):
    """When user info is changed, also updates LDAP user."""

    username = USERNAME_FIELD
    ssh_keys = forms.CharField(
        label=gettext_lazy('Authorized SSH Keys'), required=False,
        widget=forms.Textarea, help_text=gettext_lazy(
            'Setting an SSH public key will allow this user to '
            'securely log in to the system without using a '
            'password. You may enter multiple keys, one on each '
            'line. Blank lines and lines starting with # will be '
            'ignored.'))

    language = plinth.forms.LanguageSelectionFormMixin.language

    class Meta:
        """Metadata to control automatic form building."""

        fields = ('username', 'groups', 'ssh_keys', 'language', 'is_active',
                  'confirm_password')
        model = User
        widgets = {
            'groups': plinth.forms.CheckboxSelectMultipleWithReadOnly(),
        }

    def __init__(self, request, username, *args, **kwargs):
        """Initialize the form with extra request argument."""
        group_choices = dict(UsersAndGroups.get_group_choices())
        for group in group_choices:
            Group.objects.get_or_create(name=group)

        self.request = request
        self.username = username
        super().__init__(*args, **kwargs)
        self.is_last_admin_user = get_last_admin_user() == self.username
        self.fields['username'].widget.attrs.update({
            'autofocus': 'autofocus',
            'autocapitalize': 'none',
            'autocomplete': 'username'
        })

        choices = []
        django_groups = sorted(self.fields['groups'].choices,
                               key=lambda choice: choice[1])
        for group_id, group_name in django_groups:
            try:
                group_id = group_id.value
            except AttributeError:
                pass

            # Show choices only from groups declared by apps.
            if group_name in group_choices:
                label = group_choices[group_name]
                if group_name == 'admin' and self.is_last_admin_user:
                    label = {'label': label, 'disabled': True}

                choices.append((group_id, label))

        self.fields['groups'].label = _('Permissions')
        self.fields['groups'].choices = choices

        if not is_user_admin(request):
            self.fields['is_active'].widget = forms.HiddenInput()
            self.fields['groups'].disabled = True

        if self.is_last_admin_user:
            self.fields['is_active'].disabled = True

    def save(self, commit=True):
        """Update LDAP user name and groups after saving user model."""
        user = super().save(commit=False)
        # Profile is auto saved with user object
        user.userprofile.language = self.cleaned_data['language']
        auth_username = self.request.user.username
        confirm_password = self.cleaned_data['confirm_password']

        if commit:
            user.save()
            self.save_m2m()

            old_groups = privileged.get_user_groups(self.username)
            old_groups = [group for group in old_groups if group]

            if self.username != user.get_username():
                try:
                    privileged.rename_user(self.username, user.get_username())
                except Exception:
                    messages.error(self.request,
                                   _('Renaming LDAP user failed.'))

            new_groups = user.groups.values_list('name', flat=True)
            for old_group in old_groups:
                if old_group not in new_groups:
                    try:
                        privileged.remove_user_from_group(
                            user.get_username(), old_group, auth_username,
                            confirm_password)
                    except Exception:
                        messages.error(self.request,
                                       _('Failed to remove user from group.'))

            for new_group in new_groups:
                if new_group not in old_groups:
                    try:
                        privileged.add_user_to_group(user.get_username(),
                                                     new_group, auth_username,
                                                     confirm_password)
                    except Exception:
                        messages.error(self.request,
                                       _('Failed to add user to group.'))

            try:
                ssh_privileged.set_keys(user.get_username(),
                                        self.cleaned_data['ssh_keys'].strip(),
                                        auth_username, confirm_password)
            except Exception:
                messages.error(self.request, _('Unable to set SSH keys.'))

            is_active = self.cleaned_data['is_active']
            if self.initial['is_active'] != is_active:
                if is_active:
                    status = 'active'
                else:
                    status = 'inactive'
                try:
                    privileged.set_user_status(user.get_username(), status,
                                               auth_username, confirm_password)
                except Exception:
                    messages.error(self.request,
                                   _('Failed to change user status.'))

        return user

    def clean_groups(self):
        """Validate groups to ensure admin group for last admin.

        For the last admin user, we disable the checkbox for 'admin' group so
        that it can't be unchecked. However, this means that browser will no
        longer submit that value. Forcefully add 'admin' group in this case.

        """
        groups = self.cleaned_data['groups']
        if self.is_last_admin_user:
            groups = groups | self.fields['groups'].queryset.filter(
                **{'name': 'admin'})

        return groups


class UserChangePasswordForm(PasswordConfirmForm, SetPasswordForm):
    """Custom form that also updates password for LDAP users."""

    def __init__(self, request, *args, **kwargs):
        """Initialize the form with extra request argument."""
        self.request = request
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update(
            {'autofocus': 'autofocus'})

    def save(self, commit=True):
        """Save the user model and change LDAP password as well."""
        user = super().save(commit)
        auth_username = self.request.user.username
        if commit:
            try:
                privileged.set_user_password(
                    user.get_username(), self.cleaned_data['new_password1'],
                    auth_username, self.cleaned_data['confirm_password'])
            except Exception:
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
                privileged.create_user(user.get_username(),
                                       self.cleaned_data['password1'])
            except Exception as error:
                messages.error(
                    self.request,
                    _('Creating LDAP user failed: {error}'.format(
                        error=error)))

            try:
                privileged.add_user_to_group(user.get_username(), 'admin')
            except Exception as error:
                messages.error(
                    self.request,
                    _('Failed to add new user to admin group: {error}'.format(
                        error=error)))

            # Create initial Django groups
            for group_choice in UsersAndGroups.get_group_choices():
                auth.models.Group.objects.get_or_create(name=group_choice[0])

            admin_group = auth.models.Group.objects.get(name='admin')
            admin_group.user_set.add(user)

            self.login_user(self.cleaned_data['username'],
                            self.cleaned_data['password1'])

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
