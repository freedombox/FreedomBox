# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring Ejabberd.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy


class EjabberdForm(forms.Form):
    """Ejabberd configuration form."""
    MAM_enabled = forms.BooleanField(
        label=_('Enable Message Archive Management'), required=False,
        help_text=format_lazy(
            _('If enabled, your {box_name} will store chat message histories. '
              'This allows synchronization of conversations between multiple '
              'clients, and reading the history of a multi-user chat room. '
              'It depends on the client settings whether the histories are '
              'stored as plain text or encrypted.'), box_name=_(cfg.box_name)))
