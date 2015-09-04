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
from gettext import gettext as _
import glob
import re


class DateTimeForm(forms.Form):
    """Date/time configuration form."""
    enabled = forms.BooleanField(
        label=_('Enable network time'),
        required=False)

    time_zone = forms.ChoiceField(
        label=_('Time Zone'),
        help_text=_('Set your time zone to get accurate timestamps. \
This will set the systemwide time zone.'))

    def __init__(self, *args, **kwargs):
        """Initialize the date/time form."""
        forms.Form.__init__(self, *args, **kwargs)

        time_zone_options = [(zone, zone)
                             for zone in self.get_time_zones()]
        # Show not-set option only when time zone is not set
        if self.initial.get('time_zone') == 'none':
            time_zone_options.insert(0, ('none', _('-- no time zone set --')))

        self.fields['time_zone'].choices = time_zone_options

    @staticmethod
    def get_time_zones():
        """Return list of available time zones"""
        time_zones = []
        for line in open('/usr/share/zoneinfo/zone.tab'):
            if re.match(r'^(#|\s*$)', line):
                continue

            try:
                time_zones.append(line.split()[2])
            except IndexError:
                pass

        time_zones.sort()

        additional_time_zones = [
            path[len('/usr/share/zoneinfo/'):]
            for path in glob.glob('/usr/share/zoneinfo/Etc/*')]

        # Add additional time zones at the top to make them more
        # noticeable because people won't look for them
        return additional_time_zones + time_zones
