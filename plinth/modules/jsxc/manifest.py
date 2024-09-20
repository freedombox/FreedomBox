# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('JSXC'),
    'platforms': [{
        'type': 'web',
        'url': reverse_lazy('jsxc:jsxc')
    }]
}]

backup: dict = {}

tags = [_('XMPP'), _('Client')]
