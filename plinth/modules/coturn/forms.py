# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for Coturn app.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from plinth.modules import coturn
from plinth.modules.coturn.components import TurnConfiguration


def get_domain_choices():
    """Double domain entries for inclusion in the choice field."""
    return ((domain, domain) for domain in coturn.get_available_domains())


def turn_uris_validator(turn_uris):
    """Validate list of STUN/TURN Server URIs."""
    uris = [uri for uri in turn_uris.split('\r\n') if uri]
    if not TurnConfiguration.validate_turn_uris(uris):
        raise ValidationError(_('Invalid list of STUN/TURN Server URIs'))


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
