# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for Coturn app.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.modules import coturn


def get_domain_choices():
    """Double domain entries for inclusion in the choice field."""
    return ((domain, domain) for domain in coturn.get_available_domains())


class CoturnForm(forms.Form):
    """Form to select a TLS domain for Coturn."""

    domain = forms.ChoiceField(
        choices=get_domain_choices,
        label=_('TLS domain'),
        help_text=_(
            'Select a domain to use TLS with. If the list is empty, please '
            'configure at least one domain with certificates.'),
        required=False,
    )
