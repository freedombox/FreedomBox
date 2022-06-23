# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring MediaWiki.
"""

import pathlib

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _


def get_skins():
    """Return a list of available skins as choice field values."""
    skins_dir = pathlib.Path('/var/lib/mediawiki/skins')
    if not skins_dir.exists():
        return []

    return [(skin.name.lower(), skin.name) for skin in skins_dir.iterdir()
            if skin.is_dir()]


class MediaWikiForm(forms.Form):  # pylint: disable=W0232
    """MediaWiki configuration form."""
    password = forms.CharField(
        label=_('Administrator Password'), help_text=_(
            'Set a new password for MediaWiki\'s administrator account '
            '(admin). The password cannot be a common one and the minimum '
            'required length is <strong>10 characters</strong>. '
            'Leave this field blank to keep the current password.'),
        required=False, widget=forms.PasswordInput, min_length=10)

    domain = forms.CharField(
        label=_('Domain'), required=False, help_text=_(
            'Used by MediaWiki to generate URLs that point to the wiki '
            'such as in footer, feeds and emails. Examples: '
            '"myfreedombox.example.org" or "example.onion".'))

    site_name = forms.CharField(
        label=_('Site Name'), required=False,
        help_text=_('Name of the site as displayed throughout the wiki.'),
        validators=[validators.RegexValidator('[$"]', inverse_match=True)])

    enable_public_registrations = forms.BooleanField(
        label=_('Enable public registrations'), required=False,
        help_text=_('If enabled, anyone on the internet will be able to '
                    'create an account on your MediaWiki instance.'))

    enable_private_mode = forms.BooleanField(
        label=_('Enable private mode'), required=False,
        help_text=_('If enabled, access will be restricted. Only people '
                    'who have accounts can read/write to the wiki. '
                    'Public registrations will also be disabled.'))

    default_skin = forms.ChoiceField(
        label=_('Default Skin'), required=False,
        help_text=_('Choose a default skin for your MediaWiki installation. '
                    'Users have the option to select their preferred skin.'),
        choices=get_skins)
