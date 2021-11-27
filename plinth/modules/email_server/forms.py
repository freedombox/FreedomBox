# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the email app.
"""
import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from . import aliases as aliases_module

domain_validator = RegexValidator(r'^[A-Za-z0-9-\.]+$',
                                  _('Enter a valid domain'))
destination_validator = RegexValidator(
    r'^[ -~]+$',  # ASCII chars from 32 to 126
    _('Enter a valid destination'))


class EmailServerForm(forms.Form):
    domain = forms.CharField(label=_('domain'), max_length=256)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DomainsForm(forms.Form):
    _mailname = forms.CharField(required=True, strip=True,
                                validators=[domain_validator])
    mydomain = forms.CharField(required=True, strip=True,
                               validators=[domain_validator])
    myhostname = forms.CharField(required=True, strip=True,
                                 validators=[domain_validator])
    mydestination = forms.CharField(required=True, strip=True,
                                    validators=[destination_validator])

    def clean(self):
        """Convert values to lower case."""
        data = self.cleaned_data
        if '_mailname' in data:
            data['_mailname'] = data['_mailname'].lower()

        if 'myhostname' in data:
            data['myhostname'] = data['myhostname'].lower()

        if 'mydestination' in data:
            data['mydestination'] = data['mydestination'].lower()


class AliasCreateForm(forms.Form):
    """Form to create a new alias."""
    alias = forms.CharField(label=_('New alias (without @domain)'),
                            min_length=2, max_length=50)

    def clean_alias(self):
        """Return the checked value for alias."""
        value = self.data['alias'].strip().lower()
        if not re.match('^[a-z0-9-_\\.]+$', value):
            raise ValidationError(_('Contains illegal characters'))

        if not re.match('^[a-z0-9].*[a-z0-9]$', value):
            raise ValidationError(_('Must start and end with a-z or 0-9'))

        if re.match('^[0-9]+$', value):
            raise ValidationError(_('Cannot be a number'))

        if aliases_module.exists(value):
            raise ValidationError('Alias is already taken')

        return value


class AliasListForm(forms.Form):
    """Form to list/enable/disable/delete current aliases."""
    aliases = forms.MultipleChoiceField(label=_('Aliases'),
                                        widget=forms.CheckboxSelectMultiple)

    def __init__(self, aliases, *args, **kwargs):
        """Populate the choices for aliases."""
        super().__init__(*args, **kwargs)
        enabled_aliases = [(alias.name, alias.name) for alias in aliases
                           if alias.enabled]
        disabled_aliases = [(alias.name, alias.name) for alias in aliases
                            if not alias.enabled]
        choices = []
        if enabled_aliases:
            choices.append((_('Enabled'), enabled_aliases))

        if disabled_aliases:
            choices.append((_('Disabled'), disabled_aliases))

        self.fields['aliases'].choices = choices

    def clean(self):
        """Add the pressed button to cleaned data."""
        cleaned_data = super().clean()
        buttons = [key[4:] for key in self.data if key.startswith('btn_')]
        if len(buttons) != 1 or buttons[0] not in ('enable', 'disable',
                                                   'delete'):
            raise ValidationError('Invalid button pressed')

        cleaned_data['action'] = buttons[0]
        return cleaned_data
