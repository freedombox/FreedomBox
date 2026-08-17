# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django forms for sharing app."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from plinth.modules.users.components import UsersAndGroups

from . import privileged


class AddShareForm(forms.Form):
    """Form to add a new share."""

    name = forms.RegexField(
        label=_('Name of the share'), strip=True, regex=r'^[a-z0-9]+$',
        help_text=_(
            'A lowercase alpha-numeric string that uniquely identifies a '
            'share. Example: <em>media</em>.'))

    path = forms.CharField(
        label=_('Path to share'), strip=True, help_text=_(
            'Disk path to a folder on this server that you intend to share.'))

    is_public = forms.BooleanField(
        label=_('Public share'), required=False, help_text=_(
            'Make files in this folder available to anyone with the link.'))

    groups = forms.MultipleChoiceField(
        choices=UsersAndGroups.get_group_choices,
        widget=forms.CheckboxSelectMultiple, required=False,
        label=_('User groups that can read the files in the share:'),
        help_text=_(
            'Users of the selected user groups will be able to read the '
            'files in the share.'))

    def __init__(self, *args, **kwargs):
        """Initialize the form with extra request argument."""
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

    def clean_name(self):
        """Check if the name is valid."""
        name = self.cleaned_data['name']
        if 'name' in self.initial and name == self.initial['name']:
            return name

        if any((share for share in privileged.list_shares()
                if name == share['name'])):
            raise ValidationError(_('A share with this name already exists.'))

        return name

    def clean(self):
        """Check that at least one group is added for non-public shares."""
        super().clean()
        is_public = self.cleaned_data.get('is_public')
        groups = self.cleaned_data.get('groups')
        if not is_public and not groups:
            raise forms.ValidationError(
                _('Shares should be either public or shared with at '
                  'least one group'))
