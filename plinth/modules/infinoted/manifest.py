# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy

clients = [{
    'name':
        _('Gobby'),
    'description':
        _('Gobby is a collaborative text editor'),
    'usage':
        format_lazy(
            _('Start Gobby and select "Connect to Server" and '
              'enter your {box_name}\'s domain name.'),
            box_name=_(cfg.box_name)),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://github.com/gobby/gobby/wiki/Download'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://github.com/gobby/gobby/wiki/Download'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'gobby'
    }]
}]

backup = {
    'data': {
        'directories': ['/var/lib/infinoted/']
    },
    'secrets': {
        'files': [
            '/etc/infinoted/infinoted-cert.pem',
            '/etc/infinoted/infinoted-key.pem'
        ],
    },
    'services': ['infinoted']
}

tags = [_('Note Taking'), _('Collaborative Editing'), _('Gobby')]
