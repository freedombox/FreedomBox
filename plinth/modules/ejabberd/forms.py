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
Forms for configuring Ejabberd.
"""

from plinth import forms as plinthForms
from django import forms as djangoForms
from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy


class EjabberdForm(plinthForms.ServiceForm):
    """Ejabberd configuration form."""
    MAM_enabled = djangoForms.BooleanField(
        label=_('Enable Message Archive Management'),
        required=False,
        help_text=format_lazy(_(
            'If enabled, your {box_name} will store chat message histories. '
            'This allows synchronization of conversations between multiple '
            'clients, and reading the history of a multi-user chat room. '
            'It depends on the client settings whether the histories are '
            'stored as plain text or encrypted.'), box_name=_(cfg.box_name)))
