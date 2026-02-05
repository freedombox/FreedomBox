# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for backups module.
"""

import logging
import os
import re
import subprocess

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import (FileExtensionValidator,
                                    validate_ipv46_address)
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.modules.storage import get_mounts
from plinth.utils import format_lazy

from . import api, split_path
from .repository import get_repositories

logger = logging.getLogger(__name__)


def _get_app_choices(components):
    """Return a list of check box multiple choices from list of components."""
    choices = []
    for component in components:
        name = str(component.app.info.name)
        if not component.has_data:
            name = gettext('{app} (No data to backup)').format(
                app=component.app.info.name)

        choices.append((component.app_id, name))

    return sorted(choices, key=lambda choice: choice[1].lower())


def _get_repository_choices():
    """Return the list of available repositories."""
    choices = [(repository.uuid, repository.name)
               for repository in get_repositories() if repository.is_usable()]

    return choices


class ScheduleForm(forms.Form):
    """Form to edit backups schedule."""

    enabled = forms.BooleanField(
        label=_('Enable scheduled backups'), required=False,
        help_text=_('If enabled, a backup is taken every day, every week and '
                    'every month. Older backups are removed.'))

    daily_to_keep = forms.IntegerField(
        label=_('Number of daily backups to keep'), required=True, min_value=0,
        help_text=_('This many latest backups are kept and the rest are '
                    'removed. A value of "0" disables backups of this type. '
                    'Triggered at specified hour every day.'))

    weekly_to_keep = forms.IntegerField(
        label=_('Number of weekly backups to keep'), required=True,
        min_value=0,
        help_text=_('This many latest backups are kept and the rest are '
                    'removed. A value of "0" disables backups of this type. '
                    'Triggered at specified hour every Sunday.'))

    monthly_to_keep = forms.IntegerField(
        label=_('Number of monthly backups to keep'), required=True,
        min_value=0,
        help_text=_('This many latest backups are kept and the rest are '
                    'removed. A value of "0" disables backups of this type. '
                    'Triggered at specified hour first day of every month.'))

    run_at_hour = forms.IntegerField(
        label=_('Hour of the day to trigger backup operation'), required=True,
        min_value=0, max_value=23, help_text=_(
            'In 24 hour format. Services may become temporarily unavailable '
            'while running backup operation at this time of the day.'))

    selected_apps = forms.MultipleChoiceField(
        label=_('Included apps'), help_text=_('Apps to include in the backup'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'has-select-all'}))

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        super().__init__(*args, **kwargs)
        components = api.get_all_components_for_backup()
        choices = _get_app_choices(components)
        self.fields['selected_apps'].choices = choices
        self.fields['selected_apps'].initial = [
            choice[0] for choice in choices
            if choice[0] not in self.initial.get('unselected_apps', [])
        ]


class CreateArchiveForm(forms.Form):
    repository = forms.ChoiceField(label=_('Repository'))
    name = forms.RegexField(
        label=_('Name'),
        help_text=_('(Optional) Set a name for this backup archive'),
        regex=r'^[^{}/]*$', required=False, strip=True)
    selected_apps = forms.MultipleChoiceField(
        label=_('Included apps'), help_text=_('Apps to include in the backup'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'has-select-all'}))

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        super().__init__(*args, **kwargs)
        components = api.get_all_components_for_backup()
        choices = _get_app_choices(components)
        self.fields['selected_apps'].choices = choices
        if not self.initial or 'selected_apps' not in self.initial:
            self.fields['selected_apps'].initial = [
                choice[0] for choice in choices
            ]
        self.fields['repository'].choices = _get_repository_choices()


class RestoreForm(forms.Form):
    selected_apps = forms.MultipleChoiceField(
        label=_('Select the apps you want to restore'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'has-select-all'}))

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        components = kwargs.pop('components')
        super().__init__(*args, **kwargs)
        choices = _get_app_choices(components)
        self.fields['selected_apps'].choices = choices
        self.fields['selected_apps'].initial = [
            choice[0] for choice in choices
        ]


class UploadForm(forms.Form):
    file = forms.FileField(
        label=_('Upload File'), required=True, validators=[
            FileExtensionValidator(
                ['gz'], _('Backup files have to be in .tar.gz format'))
        ], help_text=format_lazy(
            _('Select the backup file to upload from the local computer. This '
              'must be a file previously downloaded from the result of a '
              'successful backup on a {box_name}. It must have a .tar.gz '
              'extension.'), box_name=_(cfg.box_name)))


def repository_validator(path):
    """Validate an SSH repository path."""
    if not ('@' in path and ':' in path):
        raise ValidationError(_('Repository path format incorrect.'))

    username, hostname, dir_path = split_path(path)
    hostname = hostname.split('%')[0]

    # Validate username using Unix username regex
    if not re.match(r'[a-z0-9_][a-z0-9_-]*$', username):
        raise ValidationError(_(f'Invalid username: {username}'))

    # The hostname should either be a valid IP address or hostname
    # Follows RFC1123 (hostnames can start with digits) instead of RFC952
    hostname_re = (r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
                   r'([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')
    try:
        validate_ipv46_address(hostname)
    except ValidationError:
        if not re.match(hostname_re, hostname):
            raise ValidationError(_(f'Invalid hostname: {hostname}'))

    # Validate directory path
    if not re.match(r'[^\0]*', dir_path):
        raise ValidationError(_(f'Invalid directory path: {dir_path}'))


class EncryptedBackupsMixin(forms.Form):
    """Form to add a new backup repository."""
    encryption = forms.ChoiceField(
        label=_('Encryption'), help_text=format_lazy(
            _('"Key in Repository" means that a '
              'password-protected key is stored with the backup.')),
        choices=[('repokey', _('Key in Repository')), ('none', _('None'))])
    encryption_passphrase = forms.CharField(
        label=_('Passphrase'),
        help_text=_('Only needed when using encryption.'),
        widget=forms.PasswordInput(), required=False)
    confirm_encryption_passphrase = forms.CharField(
        label=_('Confirm Passphrase'), help_text=_('Repeat the passphrase.'),
        widget=forms.PasswordInput(), required=False)

    def clean(self):
        super().clean()
        passphrase = self.cleaned_data.get('encryption_passphrase')
        confirm_passphrase = self.cleaned_data.get(
            'confirm_encryption_passphrase')

        if passphrase != confirm_passphrase:
            raise forms.ValidationError(
                _('The entered encryption passphrases do not match'))

        if self.cleaned_data.get('encryption') != 'none' and not passphrase:
            raise forms.ValidationError(
                _('Passphrase is needed for encryption.'))

        return self.cleaned_data


encryption_fields = [
    'encryption', 'encryption_passphrase', 'confirm_encryption_passphrase'
]


def get_disk_choices():
    """Returns a list of all available partitions except the root partition."""
    repositories = get_repositories()
    existing_paths = [
        repository.path for repository in repositories
        if repository.storage_type == 'disk'
    ]
    choices = []
    for device in get_mounts():
        if device['mount_point'] == '/':
            continue

        path = os.path.join(device['mount_point'], 'FreedomBoxBackups')
        if path in existing_paths:
            continue

        name = device['label'] if device['label'] else device['mount_point']
        choices.append((device['mount_point'], name))

    return choices


class AddRepositoryForm(EncryptedBackupsMixin, forms.Form):
    """Form to create a new backups repository on a disk."""
    disk = forms.ChoiceField(
        label=_('Select Disk or Partition'), help_text=format_lazy(
            _('Backups will be stored in the directory FreedomBoxBackups')),
        choices=get_disk_choices)

    field_order = ['disk'] + encryption_fields


class AddRemoteRepositoryForm(EncryptedBackupsMixin, forms.Form):
    """Form to add new SSH remote repository."""
    repository = forms.CharField(
        label=_('SSH Repository Path'), strip=True,
        help_text=_('Path of a new or existing repository. Example: '
                    '<i>user@host:~/path/to/repo/</i>'),
        validators=[repository_validator])
    ssh_auth_type = forms.ChoiceField(
        label=_('SSH Authentication Type'),
        help_text=_('Choose how to authenticate to the remote SSH server.'),
        widget=forms.RadioSelect(),
        choices=[('key_auth', _('Key-based Authentication')),
                 ('password_auth', _('Password-based Authentication'))])
    ssh_password = forms.CharField(
        label=_('SSH server password'), widget=forms.PasswordInput(),
        strip=True, help_text=_('Required for password-based authentication.'),
        required=False)

    field_order = ['repository', 'ssh_auth_type', 'ssh_password'
                   ] + encryption_fields

    def clean(self):
        """Perform additional checks on form data."""
        super().clean()
        ssh_password = self.cleaned_data.get('ssh_password')
        if self.cleaned_data.get(
                'ssh_auth_type') == 'password_auth' and not ssh_password:
            raise forms.ValidationError(
                _('SSH password is needed for password-based authentication.'))

        return self.cleaned_data

    def clean_repository(self):
        """Validate repository form field."""
        path = self.cleaned_data.get('repository')
        # Avoid creation of duplicate ssh remotes
        self._check_if_duplicate_remote(path)
        return path

    @staticmethod
    def _check_if_duplicate_remote(path):
        """Raise validation error if given path is a stored remote."""
        for repository in get_repositories():
            if repository.path == path:
                raise forms.ValidationError(
                    _('Remote backup repository already exists.'))


class VerifySshHostkeyForm(forms.Form):
    """Form to verify the SSH public key for a host."""
    ssh_public_key = forms.ChoiceField(
        label=_('Select verified SSH public key'), widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        hostname = kwargs.pop('hostname')
        super().__init__(*args, **kwargs)
        (self.fields['ssh_public_key'].choices,
         self.keyscan_error) = self._get_all_public_keys(hostname)

    @staticmethod
    def _get_all_public_keys(hostname):
        """Use ssh-keyscan to get all the SSH public keys of a host."""
        # Fetch public keys of ssh remote
        keyscan = subprocess.run(['ssh-keyscan', hostname],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, check=False)
        key_lines = keyscan.stdout.decode().splitlines()
        keys = [line for line in key_lines if not line.startswith('#')]
        error_message = keyscan.stderr.decode() if keyscan.returncode else None
        # Generate user-friendly fingerprints of public keys
        keygen = subprocess.run(['ssh-keygen', '-l', '-f', '-'],
                                input=keyscan.stdout, stdout=subprocess.PIPE,
                                check=False)
        fingerprints = keygen.stdout.decode().splitlines()

        return zip(keys, fingerprints), error_message
