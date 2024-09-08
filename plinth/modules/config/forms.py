# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for basic system configuration
"""

import logging
import re

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from plinth import cfg, frontpage
from plinth.modules.apache import get_users_with_website
from plinth.utils import format_lazy

from . import home_page_url2scid

logger = logging.getLogger(__name__)

HOSTNAME_REGEX = r'^[a-zA-Z0-9]([-a-zA-Z0-9]{,61}[a-zA-Z0-9])?$'


def domain_label_validator(domainname):
    """Validate domain name labels."""
    for label in domainname.split('.'):
        if not re.match(HOSTNAME_REGEX, label):
            raise ValidationError(_('Invalid domain name'))


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

    domainname = forms.CharField(
        label=gettext_lazy('Domain Name'), help_text=format_lazy(
            gettext_lazy(
                'Domain name is the global name by which other devices on the '
                'Internet can reach your {box_name}.  It must consist of '
                'labels separated by dots.  Each label must start and end '
                'with an alphabet or a digit and have as interior characters '
                'only alphabets, digits and hyphens.  Length of each label '
                'must be 63 characters or less.  Total length of domain name '
                'must be 253 characters or less.'),
            box_name=gettext_lazy(cfg.box_name)), required=False, validators=[
                validators.RegexValidator(
                    r'^[a-zA-Z0-9]([-a-zA-Z0-9.]{,251}[a-zA-Z0-9])?$',
                    gettext_lazy('Invalid domain name')),
                domain_label_validator
            ], strip=True)

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
