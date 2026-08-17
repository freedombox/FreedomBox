# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for radicale module.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy

CHOICES = [
    ('owner_only',
     _('Only the owner of a calendar/addressbook can view or '
       'make changes.')),
    ('owner_write',
     format_lazy(
         _('Any user with a {box_name} login can view any calendar/addressbook'
           ', but only the owner can make changes.'),
         box_name=_(cfg.box_name))),
    ('authenticated',
     format_lazy(
         _('Any user with a {box_name} login can view or make changes'
           ' to any calendar/addressbook.'), box_name=_(cfg.box_name))),
]


class RadicaleForm(forms.Form):
    """Specialized configuration form for radicale service."""
    access_rights = forms.ChoiceField(label=_('Access rights'),
                                      choices=CHOICES, required=True,
                                      widget=forms.RadioSelect())
