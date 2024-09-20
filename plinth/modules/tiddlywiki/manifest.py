# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for TiddlyWiki."""

from django.utils.translation import gettext_lazy as _

from .privileged import wiki_dir

clients = [{
    'name': _('TiddlyWiki'),
    'platforms': [{
        'type': 'web',
        'url': '/tiddlywiki/'
    }]
}]

backup = {'data': {'directories': [str(wiki_dir)]}}

tags = [
    _('Wiki'),
    _('Note Taking'),
    _('Website'),
    _('Journal'),
    _('Digital Garden'),
    _('Zettelkasten'),
    _('Quine'),
    _('non-Debian')
]
