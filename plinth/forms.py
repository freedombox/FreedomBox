#
# This file is part of Plinth.
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
Plinth framework forms
"""

from django import forms


class PackageInstallForm(forms.Form):
    """Prompt for installation of a package.

    XXX: Don't store the package list in a hidden input as it can be
    modified on the client side.  Use session store to store and retrieve
    the package list.  It has to be form specific so that multiple
    instances of forms don't clash with each other.
    """
    package_names = forms.CharField(widget=forms.HiddenInput)
