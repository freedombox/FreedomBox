# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring MediaWiki.
"""

import json
import logging
import pathlib
import subprocess

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _

from . import privileged


def get_skins():
    """Return a list of available skins as choice field values."""
    skins_dir = pathlib.Path('/var/lib/mediawiki/skins')
    if not skins_dir.exists():
        return []

    return [(skin.name.lower(), skin.name) for skin in skins_dir.iterdir()
            if skin.is_dir()]


def get_languages():
    """Return a list of available languages as choice field values."""
    # Names.php has different locations on Bullseye Bookworm
    names_old = pathlib.Path('/usr/share/mediawiki/languages/data/Names.php')
    names_new = pathlib.Path('/usr/share/mediawiki/includes/languages/'
                             'data/Names.php')
    names_file = names_old
    if not names_old.exists():
        names_file = names_new

    script = rf'''<?php
    require_once('{names_file}');
    print(json_encode(Mediawiki\Languages\Data\Names::$names));'''
    try:
        process = subprocess.run([privileged.get_php_command()],
                                 input=script.encode(), stdout=subprocess.PIPE,
                                 check=True)
        languages_dict = json.loads(process.stdout.decode())
        return list(languages_dict.items())
    except Exception as exception:
        logging.exception('Unable read list of Mediawiki languages.',
                          exception)
        return [('en', 'English')]


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
            '"myfreedombox.example.org" or "example.onion".'),
        validators=[validators.RegexValidator('[$"]', inverse_match=True)])

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

    default_lang = forms.ChoiceField(
        label=_('Default Language'), required=False,
        help_text=_('Choose a default language for your MediaWiki '
                    'installation. Users have the option to select '
                    'their preferred language.'), choices=get_languages)
