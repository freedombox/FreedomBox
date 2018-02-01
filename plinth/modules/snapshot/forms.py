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
Forms for snapshot module.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class SnapshotForm(forms.Form):
    enable_timeline_snapshots = forms.BooleanField(
        label=_('Enable Timeline Snapshots'), required=False, help_text=_(
            'Uncheck this to disable timeline snapshots '
            '(hourly, daily, monthly and yearly).'))
    hourly_limit = forms.IntegerField(label=_('Hourly Snapshots Limit'),required=False, min_value=0)
    daily_limit = forms.IntegerField(label=_('Daily Snapshots Limit'),required=False, min_value=0)
    weekly_limit = forms.IntegerField(label=_('Weekly Snapshots Limit'),required=False, min_value=0)
    monthly_limit = forms.IntegerField(label=_('Monthly Snapshots Limit'),required=False, min_value=0)
    yearly_limit = forms.IntegerField(label=_('Yearly Snapshots Limit'),required=False, min_value=0)
    number_min_age = forms.IntegerField(label=_('Software Snapshots Minimum Age (days)'), required=False, min_value=0)
