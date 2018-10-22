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

import os

from django import forms
from django.core import validators
from django.core.validators import FileExtensionValidator
from django.utils.translation import ugettext, ugettext_lazy as _

from . import api
from . import get_export_locations, get_archive_path, get_location_path


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


class CreateArchiveForm(forms.Form):
    name = forms.CharField(
        label=_('Archive name'), strip=True,
        help_text=_('Name for new backup archive.'), validators=[
            validators.RegexValidator(r'^[^/]+$', _('Invalid archive name'))
        ])

    selected_apps = forms.MultipleChoiceField(
        label=_('Included apps'), help_text=_('Apps to include in the backup'),
        widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        super().__init__(*args, **kwargs)
        apps = api.get_all_apps_for_backup()
        self.fields['selected_apps'].choices = _get_app_choices(apps)
        self.fields['selected_apps'].initial = [app.name for app in apps]


class ExportArchiveForm(forms.Form):
    disk = forms.ChoiceField(
        label=_('Disk'), widget=forms.RadioSelect(),
        help_text=_('Disk or removable storage where the backup archive will '
                    'be saved.'))

    def __init__(self, *args, **kwargs):
        """Initialize the form with disk choices."""
        super().__init__(*args, **kwargs)
        self.fields['disk'].choices = [(location['device'], location['label'])
                                       for location in get_export_locations()]


class RestoreForm(forms.Form):
    selected_apps = forms.MultipleChoiceField(
        label=_('Restore apps'),
        help_text=_('Apps data to restore from the backup'),
        widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        """Initialize the form with selectable apps."""
        apps = kwargs.pop('apps')
        super().__init__(*args, **kwargs)
        self.fields['selected_apps'].choices = _get_app_choices(apps)
        self.fields['selected_apps'].initial = [app.name for app in apps]


class UploadForm(forms.Form):
    location = forms.ChoiceField(
        choices=(), label=_('Location'), initial='', widget=forms.Select(),
        required=True, help_text=_('Location to upload the archive to'))
    file = forms.FileField(
        label=_('Upload File'), required=True, validators=[
            FileExtensionValidator(['gz'],
                                   'Backup files have to be in .tar.gz format')
        ], help_text=_('Select the backup file you want to upload'))

    def __init__(self, *args, **kwargs):
        """Initialize the form with location choices."""
        super().__init__(*args, **kwargs)
        locations = get_export_locations()
        # users should only be able to select a location name -- don't
        # provide paths as a form input for security reasons
        location_labels = [(location['device'], location['label'])
                           for location in locations]
        self.fields['location'].choices = location_labels

    def clean(self):
        """Check that the uploaded file does not yet exist."""
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        location_device = cleaned_data.get('location')
        location_path = get_location_path(location_device)
        # if other errors occured before, 'file' won't be in cleaned_data
        if (file and file.name):
            filepath = get_archive_path(location_path, file.name)
            if os.path.exists(filepath):
                raise forms.ValidationError(
                    "File %s already exists" % file.name)
            else:
                self.cleaned_data.update({'filepath': filepath})
