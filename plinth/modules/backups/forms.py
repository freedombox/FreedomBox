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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Forms for backups module.
"""

import logging
import os
import re
import subprocess
import tempfile

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import (FileExtensionValidator,
                                    validate_ipv46_address)
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from plinth.utils import format_lazy

from . import ROOT_REPOSITORY_NAME, api, network_storage, split_path

logger = logging.getLogger(__name__)


def _get_app_choices(apps):
    """Return a list of check box multiple choices from list of apps."""
    choices = []
    for app in apps:
        name = app.app.name
        if not app.has_data:
            name = ugettext('{app} (No data to backup)').format(
                app=app.app.name)

        choices.append((app.name, name))

    return choices


def _get_repository_choices():
    """Return the list of available repositories."""
    choices = [('root', ROOT_REPOSITORY_NAME)]
    storages = network_storage.get_storages()
    for storage in storages.values():
        if storage['verified']:
            choices += [(storage['uuid'], storage['path'])]

    return choices


class CreateArchiveForm(forms.Form):
    repository = forms.ChoiceField()
    selected_apps = forms.MultipleChoiceField(
        label=_('Included apps'), help_text=_('Apps to include in the backup'),
        widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        super().__init__(*args, **kwargs)
        apps = api.get_all_apps_for_backup()
        self.fields['selected_apps'].choices = _get_app_choices(apps)
        self.fields['selected_apps'].initial = [app.name for app in apps]
        self.fields['repository'].choices = _get_repository_choices()


class RestoreForm(forms.Form):
    selected_apps = forms.MultipleChoiceField(
        label=_('Select the apps you want to restore'),
        widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        apps = kwargs.pop('apps')
        super().__init__(*args, **kwargs)
        self.fields['selected_apps'].choices = _get_app_choices(apps)
        self.fields['selected_apps'].initial = [app.name for app in apps]


class UploadForm(forms.Form):
    file = forms.FileField(
        label=_('Upload File'), required=True, validators=[
            FileExtensionValidator(
                ['gz'], _('Backup files have to be in .tar.gz format'))
        ], help_text=_('Select the backup file you want to upload'))


def repository_validator(path):
    """Validate an SSH repository path."""
    if not ('@' in path and ':' in path):
        raise ValidationError(_('Repository path format incorrect.'))

    username, hostname, dir_path = split_path(path)
    hostname = hostname.split('%')[0]

    # Validate username using Unix username regex
    if not re.match(r'[a-z_][a-z0-9_-]*$', username):
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


class AddRepositoryForm(forms.Form):
    """Form to add new SSH remote repository."""
    repository = forms.CharField(
        label=_('SSH Repository Path'), strip=True,
        help_text=_('Path of a new or existing repository. Example: '
                    '<i>user@host:~/path/to/repo/</i>'),
        validators=[repository_validator])
    ssh_password = forms.CharField(
        label=_('SSH server password'), strip=True,
        help_text=_('Password of the SSH Server.<br />'
                    'SSH key-based authentication is not yet possible.'),
        widget=forms.PasswordInput(), required=False)
    encryption = forms.ChoiceField(
        label=_('Encryption'), help_text=format_lazy(
            _('"Key in Repository" means that a '
              'password-protected key is stored with the backup.')),
        choices=[('repokey', 'Key in Repository'), ('none', 'None')])
    encryption_passphrase = forms.CharField(
        label=_('Passphrase'),
        help_text=_('Passphrase; Only needed when using encryption.'),
        widget=forms.PasswordInput(), required=False)
    confirm_encryption_passphrase = forms.CharField(
        label=_('Confirm Passphrase'), help_text=_('Repeat the passphrase.'),
        widget=forms.PasswordInput(), required=False)

    def clean(self):
        super(AddRepositoryForm, self).clean()
        passphrase = self.cleaned_data.get('encryption_passphrase')
        confirm_passphrase = self.cleaned_data.get(
            'confirm_encryption_passphrase')

        if passphrase != confirm_passphrase:
            raise forms.ValidationError(
                _('The entered encryption passphrases do not match'))

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
        for storage in network_storage.get_storages().values():
            if storage['path'] == path:
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
        self.fields['ssh_public_key'].choices = self._get_all_public_keys(
            hostname)

    @staticmethod
    def _get_all_public_keys(hostname):
        """Use ssh-keyscan to get all the SSH public keys of a host."""
        # Fetch public keys of ssh remote
        res1 = subprocess.run(['ssh-keyscan', hostname],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, check=True)

        with tempfile.NamedTemporaryFile(delete=False) as tmpfil:
            tmpfil.write(res1.stdout)

        # Generate user-friendly fingerprints of public keys
        res2 = subprocess.run(['ssh-keygen', '-l', '-f', tmpfil.name],
                              stdout=subprocess.PIPE)
        os.remove(tmpfil.name)
        keys = res2.stdout.decode().splitlines()

        # Create a list of tuples of (algorithm, fingerprint)
        return [(key.rsplit(' ', 1)[-1].strip('()'), key) for key in keys]
