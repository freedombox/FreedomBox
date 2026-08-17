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
            _('When enabled, users can only read and send mails via this '
              '{box_name}. If you wish to use Roundcube with an external mail '
              'account, such as Gmail, you must uncheck this option. When '
              'unchecked, a text entry field is added to the login page so '
              'the user can specify to which account they wish to connect.'),
            box_name=_(cfg.box_name)), required=False)
