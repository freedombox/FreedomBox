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
FreedomBox app for configuring Transmission.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.modules.transmission import reserved_usernames
from plinth.modules.storage.forms import (DirectorySelectForm,
                                          DirectoryValidator)


class TransmissionForm(DirectorySelectForm):
    """Transmission configuration form"""

    def __init__(self, *args, **kw):
        validator = DirectoryValidator(
            username=reserved_usernames[0], check_writable=True)
        super(TransmissionForm, self).__init__(
            title=_('Download directory'),
            default='/var/lib/transmission-daemon/downloads/',
            validator=validator, *args, **kw)
