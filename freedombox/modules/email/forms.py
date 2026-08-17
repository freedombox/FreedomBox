# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for the email app."""

import re
from typing import Iterator

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from plinth.modules.names.components import DomainName

from . import aliases as aliases_module


def _get_domain_choices() -> Iterator[tuple[str, str]]:
    """Double domain entries for inclusion in the choice field."""
    return ((domain.name, domain.name) for domain in DomainName.list())


class DomainForm(forms.Form):
    primary_domain = forms.ChoiceField(
        choices=_get_domain_choices,
        label=_('Primary domain'),
        help_text=_(
            'Mails are received for all domains configured in the system. '
            'Among these, select the most important one.'),
        required=True,
    )


class AliasCreateForm(forms.Form):
    """Form to create a new alias."""
    alias = forms.CharField(label=_('New alias (without @domain)'),
                            min_length=2, max_length=50)

    def clean_alias(self):
        """Return the checked value for alias."""
        value = self.data['alias'].strip().lower()
        if not re.match(r'^[a-z0-9-_\.]+$', value):
            raise ValidationError(_('Contains illegal characters'))

        if not re.match(r'^[a-z0-9].*[a-z0-9]$', value):
            raise ValidationError(_('Must start and end with a-z or 0-9'))

        # For when uids are automatically aliased to username
        if re.match(r'^[0-9]+$', value):
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
        choices = [(alias.name, alias.name) for alias in aliases]
        self.fields['aliases'].choices = choices
