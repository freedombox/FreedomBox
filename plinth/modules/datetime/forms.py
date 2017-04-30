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
Forms for configuring date and time
"""

from django import forms
from django.utils.translation import ugettext_lazy as _
import logging
import subprocess

from plinth.forms import ServiceForm


logger = logging.getLogger(__name__)


class DateTimeForm(ServiceForm):
    """Date/time configuration form."""
    time_zone = forms.ChoiceField(
        label=_('Time Zone'),
        help_text=_('Set your time zone to get accurate timestamps. \
This will set the system-wide time zone.'))

    def __init__(self, *args, **kwargs):
        """Initialize the date/time form."""
        forms.Form.__init__(self, *args, **kwargs)

        time_zone_options = [(zone, zone)
                             for zone in self.get_time_zones()]
        # Show not-set option only when time zone is not set
        current_time_zone = self.initial.get('time_zone')
        if current_time_zone == 'none':
            time_zone_options.insert(0, ('none', _('-- no time zone set --')))
        elif (current_time_zone, current_time_zone) not in time_zone_options:
            time_zone_options.insert(0, (current_time_zone, current_time_zone))

        self.fields['time_zone'].choices = time_zone_options

    @staticmethod
    def get_time_zones():
        """Return the list time zones."""
        command = ['timedatectl', 'list-timezones']
        try:
            process = subprocess.run(command, stdout=subprocess.PIPE,
                                     check=True)
        except subprocess.CalledProcessError as exception:
            logger.exception('Error getting time zones: %s', exception)
            return []

        output = process.stdout.decode()
        return output.splitlines()
