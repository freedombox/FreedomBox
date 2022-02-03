# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configuration forms for roundcube.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy


class RoundcubeForm(forms.Form):
    """Roundcube configuration form."""
    local_only = forms.BooleanField(
        label=_('Use only the local mail server'), help_text=format_lazy(
            _('When enabled, text box for server input is removed from login '
              'page and users can only read and send mails from this '
              '{box_name}.'), box_name=_(cfg.box_name)), required=False)
