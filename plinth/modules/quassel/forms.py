# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for Quassel app.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm
from plinth.modules import quassel


def get_domain_choices():
    """Double domain entries for inclusion in the choice field."""
    return ((domain, domain) for domain in quassel.get_available_domains())


class QuasselForm(AppForm):
    """Form to select a TLS domain for Quassel."""

    domain = forms.ChoiceField(
        choices=get_domain_choices,
        label=_('TLS domain'),
        help_text=_(
            'Select a domain to use TLS with. If the list is empty, please '
            'configure at least one domain with certificates.'),
    )
