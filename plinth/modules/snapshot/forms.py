# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for snapshot module.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class SnapshotForm(forms.Form):
    free_space = forms.ChoiceField(
        label=_('Free Disk Space to Maintain'),
        help_text=_('Maintain this percentage of free space on the disk. '
                    'If free space falls below this value, older snapshots '
                    'are removed until this much free space is regained. The '
                    'default value is 30%.'),
        choices=[(i / 100, '{}%'.format(i)) for i in range(10, 80, 10)])

    enable_timeline_snapshots = forms.ChoiceField(
        label=_('Timeline Snapshots'),
        help_text=_('Enable or disable timeline snapshots '
                    '(hourly, daily, monthly and yearly).'),
        choices=[('yes', _('Enabled')), ('no', _('Disabled'))])

    enable_software_snapshots = forms.ChoiceField(
        label=_('Software Installation Snapshots'),
        help_text=_('Enable or disable snapshots before and after software '
                    'installation'), choices=[('yes', _('Enabled')),
                                              ('no', _('Disabled'))])

    hourly_limit = forms.IntegerField(
        label=_('Hourly Snapshots Limit'), min_value=0,
        help_text=_('Keep a maximum of this many hourly snapshots.'))

    daily_limit = forms.IntegerField(
        label=_('Daily Snapshots Limit'), min_value=0,
        help_text=_('Keep a maximum of this many daily snapshots.'))

    weekly_limit = forms.IntegerField(
        label=_('Weekly Snapshots Limit'), min_value=0,
        help_text=_('Keep a maximum of this many weekly snapshots.'))

    monthly_limit = forms.IntegerField(
        label=_('Monthly Snapshots Limit'), min_value=0,
        help_text=_('Keep a maximum of this many monthly snapshots.'))

    yearly_limit = forms.IntegerField(
        label=_('Yearly Snapshots Limit'), min_value=0,
        help_text=_('Keep a maximum of this many yearly snapshots. '
                    'The default value is 0 (keep no yearly snapshot).'))
