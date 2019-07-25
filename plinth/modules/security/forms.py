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
Forms for security module
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class SecurityForm(forms.Form):
    """Security configuration form"""
    restricted_access = forms.BooleanField(
        label=_('Restrict console logins (recommended)'), required=False,
        help_text=_('When this option is enabled, only users in the "admin" '
                    'group will be able to log in to console or via SSH. '
                    'Console users may be able to access some services '
                    'without further authorization.'))
    fail2ban_enabled = forms.BooleanField(
        label=_('Fail2Ban (recommended)'), required=False,
        help_text=_('When this option is enabled, Fail2Ban will limit '
                    'brute force break-in attempts to the SSH server and '
                    'other enabled password protected internet-services.'))
