# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for the SOGo app."""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth.modules.names.components import DomainName


def _get_domain_choices():
    """Double domain entries for inclusion in the choice field."""
    return ((domain.name, domain.name) for domain in DomainName.list())


class DomainForm(forms.Form):
    domain = forms.ChoiceField(
        choices=_get_domain_choices,
        label=_('Domain'),
        help_text=_(
            'Mails are received for all domains configured in the system. '
            'Among these, select the most important one.'),
        required=True,
    )
