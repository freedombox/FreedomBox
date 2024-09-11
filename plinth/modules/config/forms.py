# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for basic system configuration
"""

from django import forms
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from plinth import cfg, frontpage
from plinth.modules.apache import get_users_with_website
from plinth.utils import format_lazy

from . import home_page_url2scid


def get_homepage_choices():
    """Return list of drop down choices for home page."""
    shortcuts = frontpage.Shortcut.list(web_apps_only=True)
    shortcut_choices = [(shortcut.component_id, shortcut.name)
                        for shortcut in shortcuts if shortcut.is_enabled()]
    uws_choices = \
        [(home_page_url2scid(url),
         format_lazy(gettext_lazy("{user}'s website"), user=user))
         for user, url in get_users_with_website().items()]
    apache_default = ('apache-default', _('Apache Default'))
    plinth = ('plinth', _('FreedomBox Service (Plinth)'))
    return [apache_default, plinth] + uws_choices + shortcut_choices


class ConfigurationForm(forms.Form):
    """Main system configuration form"""

    homepage = forms.ChoiceField(
        label=gettext_lazy('Webserver Home Page'), help_text=format_lazy(
            gettext_lazy(
                'Choose the default page that must be served when '
                'someone visits your {box_name} on the web. A typical use '
                'case is to set your blog or wiki as the home page when '
                'someone visits the domain name. Note that once the home '
                'page is set to something other than {box_name} Service '
                '(Plinth), your users must explicitly type /plinth or '
                '/freedombox to reach {box_name} Service (Plinth).'),
            box_name=gettext_lazy(cfg.box_name)), required=False,
        choices=get_homepage_choices)

    advanced_mode = forms.BooleanField(
        label=gettext_lazy('Show advanced apps and features'), required=False,
        help_text=gettext_lazy(
            'Show apps and features that require more technical '
            'knowledge.'))

    logging_mode = forms.ChoiceField(
        label=gettext_lazy('System-wide logging'),
        choices=(('none', gettext_lazy('Disable logging, for privacy')),
                 ('volatile',
                  gettext_lazy('Keep some in memory until a restart, '
                               'for performance')),
                 ('persistent',
                  gettext_lazy('Write to disk, useful for debugging'))),
        help_text=gettext_lazy(
            'Logs contain information about who accessed the system and debug '
            'information from various services'))
