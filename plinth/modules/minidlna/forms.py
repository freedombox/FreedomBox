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
FreedomBox configuration form for MiniDLNA server.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm


class MiniDLNAServerForm(AppForm):
    """MiniDLNA server configuration form."""
    media_dir = forms.CharField(
        label=_('Media Files Directory'),
        help_text=_('Directory that MiniDLNA Server will read for content. All'
                    ' sub-directories of this will be also scanned for media '
                    'files. '
                    'If you change the default ensure that the new directory '
                    'exists and that is readable from the "minidlna" user. '
                    'Any user media directories ("/home/username/") will '
                    'usually work.'),
        required=False,
    )
