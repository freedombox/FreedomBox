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
Forms for directory selection.
"""

import json
import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from plinth import actions, module_loader
from plinth.forms import AppForm
from plinth.modules import storage


def get_available_samba_shares():
    """Get available samba shares."""
    available_shares = []
    if is_module_enabled('samba'):
        samba_shares = json.loads(
            actions.superuser_run('samba', ['get-shares']))
        if samba_shares:
            disks = storage.get_disks()
            for share in samba_shares:
                for disk in disks:
                    if share['mount_point'] == disk['mount_point']:
                        available_shares.append(share)
                        break
    return available_shares


def is_module_enabled(name):
    """Check whether a module is enabled."""
    if name in module_loader.loaded_modules:
        module = module_loader.loaded_modules['samba']
        if module.setup_helper.get_state(
        ) != 'needs-setup' and module.app.is_enabled():
            return True

    return False


class DirectoryValidator:
    username = None
    check_writable = False
    add_user_to_share_group = False
    service_to_restart = None

    def __init__(self, username=None, check_writable=None):
        if username is not None:
            self.username = username
        if check_writable is not None:
            self.check_writable = check_writable

    def __call__(self, value):
        """Validate a directory."""
        if not value.startswith('/'):
            raise ValidationError(_('Invalid directory name.'), 'invalid')

        command = ['validate-directory', '--path', value]
        if self.check_writable:
            command.append('--check-writable')

        if self.username:
            output = actions.run_as_user('storage', command,
                                         become_user=self.username)
        else:
            output = actions.run('storage', command)

        if 'ValidationError' in output:
            error_nr = int(output.strip().split()[1])
            if error_nr == 1:
                raise ValidationError(
                    _('Directory does not exist.'), 'invalid')
            elif error_nr == 2:
                raise ValidationError(_('Path is not a directory.'), 'invalid')
            elif error_nr == 3:
                raise ValidationError(
                    _('Directory is not readable by the user.'), 'invalid')
            elif error_nr == 4:
                raise ValidationError(
                    _('Directory is not writable by the user.'), 'invalid')


class DirectorySelectForm(AppForm):
    """Directory selection form."""
    storage_dir = forms.ChoiceField(choices=[], label=_('Directory'),
                                    required=True)
    storage_subdir = forms.CharField(
        label=_('Subdirectory (optional)'), required=False)

    def __init__(self, title=None, default='/', validator=DirectoryValidator,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        if title:
            self.fields['storage_dir'].label = title
        self.validator = validator
        self.default = os.path.normpath(default)
        self.set_form_data()

    def clean(self):
        """Clean and validate form data."""
        if self.cleaned_data['is_enabled'] or not self.initial['is_enabled']:
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
