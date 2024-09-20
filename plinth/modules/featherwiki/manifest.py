# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for Feather Wiki."""

from django.utils.translation import gettext_lazy as _

from .privileged import wiki_dir

clients = [{
    'name': _('Feather Wiki'),
    'platforms': [{
        'type': 'web',
        'url': '/featherwiki/'
    }]
}]

backup = {'data': {'directories': [str(wiki_dir)]}}

tags = [_('Wiki'), _('Note Taking'), _('Website'), _('Quine'), _('non-Debian')]
