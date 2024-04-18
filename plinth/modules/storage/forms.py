# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for directory selection."""

import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth.modules import storage
from plinth.modules.samba import privileged as samba_privileged

from . import privileged


def get_available_samba_shares():
    """Get available samba shares."""
    available_shares = []
    if _is_app_enabled('samba'):
        samba_shares = samba_privileged.get_shares()
        if samba_shares:
            disks = storage.get_mounts()
            for share in samba_shares:
                for disk in disks:
                    if share['mount_point'] == disk['mount_point']:
                        available_shares.append(share)
                        break
    return available_shares


def _is_app_enabled(app_id):
    """Check whether a module is enabled."""
    app = app_module.App.get(app_id)
    if not app.needs_setup() and app.is_enabled():
        return True

    return False


class DirectoryValidator:
    """Validation helper to check a directory."""

    username = None
    check_writable = False
    check_creatable = False
    add_user_to_share_group = False
    service_to_restart = None

    def __init__(self, username=None, check_writable=None,
                 check_creatable=None):
        """Initialize the validator."""
        if username is not None:
            self.username = username
        if check_writable is not None:
            self.check_writable = check_writable
        if check_creatable is not None:
            self.check_creatable = check_creatable

    def __call__(self, value):
        """Validate a directory."""
        if not value.startswith('/'):
            raise ValidationError(_('Invalid directory name.'), 'invalid')

        try:
            if not self.username:
                raise ValueError('Invalid username for directory validator')

            privileged.validate_directory(value, self.check_creatable,
                                          self.check_writable,
                                          _run_as_user=self.username)
        except FileNotFoundError:
            raise ValidationError(_('Directory does not exist.'), 'invalid')
        except NotADirectoryError:
            raise ValidationError(_('Path is not a directory.'), 'invalid')
        except PermissionError as exception:
            if exception.args[0] == 'read':
                raise ValidationError(
                    _('Directory is not readable by the user.'), 'invalid')
            else:
                raise ValidationError(
                    _('Directory is not writable by the user.'), 'invalid')


class DirectorySelectForm(forms.Form):
    """Directory selection form."""
    storage_dir = forms.ChoiceField(choices=[], label=_('Directory'),
                                    required=True)
    storage_subdir = forms.CharField(label=_('Subdirectory (optional)'),
                                     required=False)

    def __init__(self, title=None, help_text='', default='/',
                 validator=DirectoryValidator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['storage_dir'].label = title
        self.fields['storage_dir'].help_text = help_text
        self.validator = validator
        self.default = default
        self.set_form_data()

    def clean(self):
        """Clean and validate form data."""
        storage_dir = self.cleaned_data['storage_dir']
        storage_subdir = self.cleaned_data['storage_subdir']
        if storage_dir != '/':
            storage_subdir = storage_subdir.lstrip('/')
        storage_path = os.path.realpath(
            os.path.join(storage_dir, storage_subdir))
        if self.validator:
            self.validator(storage_path)
        self.cleaned_data.update({'storage_path': storage_path})

    def get_initial(self, choices):
        """Get initial form data."""
        initial_selection = ()
        subdir = ''
        storage_path = self.initial['storage_path']
        for choice in choices:
            if storage_path.startswith(choice[0]):
                initial_selection = choice
                subdir = storage_path.split(choice[0], 1)[1].strip('/')
                if choice[0] == '/':
                    subdir = '/' + subdir
                break
        return (initial_selection, subdir)

    def set_form_data(self):
        """Set initial form data."""
        choices = []
        if self.default:
            choices = choices + [(self.default, '{0}: {1}'.format(
                _('Default'), self.default))]
        available_shares = get_available_samba_shares()
        for share in available_shares:
            if share['share_type'] != 'home':
                share_type = _('Share')
                if share['share_type'] == 'group':
                    share_type = _('Group Share')
                elif share['share_type'] == 'open':
                    share_type = _('Open Share')
                selection_text = 'Samba {0} ({1}): {2}'.format(
                    share_type, share['name'], share['path'])
                choices = choices + [(share['path'], selection_text)]
        choices = choices + [('/', _('Other directory (specify below)'))]

        initial_value, subdir = self.get_initial(choices)

        self.fields['storage_dir'].choices = choices
        self.initial['storage_dir'] = initial_value
        self.initial['storage_subdir'] = subdir
