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

from django import forms
from django.utils.translation import ugettext_lazy as _


class CreateArchiveForm(forms.Form):
    name = forms.CharField(label=_('Archive name'), strip=True,
                           help_text=_('Name for new backup archive.'))

    path = forms.CharField(label=_('Path'), strip=True, help_text=_(
        'Disk path to a folder on this server that will be archived into '
        'backup repository.'))


class ExtractArchiveForm(forms.Form):
    path = forms.CharField(label=_('Path'), strip=True, help_text=_(
        'Disk path to a folder on this server where the archive will be '
        'extracted.'))


class ExportArchiveForm(forms.Form):
    filename = forms.CharField(
        label=_('Exported filename'), strip=True,
        help_text=_('Name for the tar file exported from the archive.'))
