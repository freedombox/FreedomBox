# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import store_url
from plinth.modules import diaspora
from plinth.utils import format_lazy

clients = [{
    'name':
        _('dandelion*'),
    'description':
        _('It is an unofficial webview based client for the '
          'community-run, distributed social network diaspora*'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.github.dfa.diaspora_android'),
    }]
}, {
    'name':
        _('diaspora*'),
    'platforms': [{
        'type':
            'web',
        'url':
            format_lazy(
                'https://diaspora.{host}',
                host=diaspora.get_configured_domain_name()
                if diaspora.is_setup() else "<please-setup-domain-name>")
    }]
}]
