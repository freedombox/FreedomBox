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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Forms for configuring Tor.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy


class TorForm(forms.Form):  # pylint: disable=W0232
    """Tor configuration form."""
    enabled = forms.BooleanField(
        label=_('Enable Tor'),
        required=False)
    hs_enabled = forms.BooleanField(
        label=_('Enable Tor Hidden Service'),
        required=False,
        help_text=format_lazy(_(
            'A hidden service will allow {box_name} to provide selected '
            'services (such as ownCloud or chat) without revealing its '
            'location.'), box_name=_(cfg.box_name)))
    apt_transport_tor_enabled = forms.BooleanField(
        label=_('Download software packages over Tor'),
        required=False,
        help_text=_('When enabled, software will be downloaded over the Tor '
                    'network for installations and upgrades. This adds a '
                    'degree of privacy and security during software '
                    'downloads.'))
