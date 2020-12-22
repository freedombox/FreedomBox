# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring MediaWiki.
"""

import pathlib

from django import forms
from django.forms import Widget
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


def get_skins():
    """Return a list of available skins as choice field values."""
    skins_dir = pathlib.Path('/var/lib/mediawiki/skins')
    if not skins_dir.exists():
        return []

    return [(skin.name.lower(), skin.name) for skin in skins_dir.iterdir()
            if skin.is_dir()]


class PrependWidget(Widget):
    """Widget to create input-groups with prepended text."""

    def __init__(self, base_widget, data, *args, **kwargs):
        """Initialize widget and get base instance"""
        super(PrependWidget, self).__init__(*args, **kwargs)
        self.base_widget = base_widget(*args, **kwargs)
        self.data = data

    def render(self, name, value, attrs=None, renderer=None):
        """Render base widget and add bootstrap spans."""
        attrs['class'] = 'form-control'
        field = self.base_widget.render(name, value, attrs, renderer)
        widget_html = '''
            <div class="input-group">
              <span class="input-group-prepend">
                <span class="input-group-text">
                  %(data)s
                </span>
              </span>
              %(field)s
            </div>'''
        return mark_safe((widget_html) % {'field': field, 'data': self.data})


class MediaWikiForm(forms.Form):  # pylint: disable=W0232
    """MediaWiki configuration form."""
    password = forms.CharField(
        label=_('Administrator Password'), help_text=_(
            'Set a new password for MediaWiki\'s administrator account '
            '(admin). Leave this field blank to keep the current password.'),
        required=False, widget=forms.PasswordInput)

    server_url = forms.CharField(
        label=_('Server URL'), required=False, help_text=_(
            'Used by MediaWiki to generate URLs that point to the wiki '
            'such as in footer, feeds and emails.'),
        widget=PrependWidget(base_widget=forms.TextInput, data='https://'))

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
