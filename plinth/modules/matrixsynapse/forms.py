# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the Matrix Synapse module.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm


class MatrixSynapseForm(AppForm):
    enable_public_registration = forms.BooleanField(
        label=_('Enable Public Registration'), required=False, help_text=_(
            'Enabling public registration means that anyone on the Internet '
            'can register a new account on your Matrix server. Disable this '
            'if you only want existing users to be able to use it.'))
