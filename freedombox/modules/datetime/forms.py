# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring date and time
"""

import logging
import subprocess

from django import forms
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class DateTimeForm(forms.Form):
    """Date/time configuration form."""
    time_zone = forms.ChoiceField(
        label=_('Time Zone'),
        help_text=_('Set your time zone to get accurate timestamps. '
                    'This will set the system-wide time zone.'))

    def __init__(self, *args, **kwargs):
        """Initialize the date/time form."""
        forms.Form.__init__(self, *args, **kwargs)

        time_zone_options = [(zone, zone) for zone in self.get_time_zones()]
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
