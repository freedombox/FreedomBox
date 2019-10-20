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
"""
Django form for configuring Gitweb.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from plinth.modules import gitweb


class EditRepoForm(forms.Form):
    """Form to create and edit a new repository."""

    name = forms.RegexField(
        label=_('Name of the repository'),
        strip=True,
        regex=r'^[a-zA-Z0-9-._]+$',
        help_text=_(
            'An alpha-numeric string that uniquely identifies a repository.'),
    )

    description = forms.CharField(
        label=_('Description of the repository'), strip=True, required=False,
        help_text=_('Optional, for displaying on Gitweb.'))

    owner = forms.CharField(
        label=_('Repository\'s owner name'), strip=True, required=False,
        help_text=_('Optional, for displaying on Gitweb.'))

    is_private = forms.BooleanField(
        label=_('Private repository'), required=False,
        help_text=_('Allow only authorized users to access this repository.'))

    def __init__(self, *args, **kwargs):
        """Initialize the form with extra request argument."""
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

    def clean_name(self):
        """Check if the name is valid."""
        name = self.cleaned_data['name']
        if 'name' in self.initial and name == self.initial['name']:
            return name

        if name.endswith('.git'):
            name = name[:-4]

        if (not name) or name.startswith(('-', '.')):
            raise ValidationError(_('Invalid repository name.'))

        for repo in gitweb.app.get_repo_list():
            if name == repo['name']:
                raise ValidationError(
                    _('A repository with this name already exists.'))

        return name
