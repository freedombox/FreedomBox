#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.utils.translation import ugettext_lazy as _

from plinth.templatetags.plinth_extras import Mobile_OS, Store
from plinth.utils import format_lazy

from . import get_configured_domain_name

clients = [{
    'name':
        _('dandelion*'),
    'description':
        _('It is an unofficial webview based client for the '
          'community-run, distributed social network diaspora*'),
    'platforms': [{
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'os_version': '>4.2.0',
        'store_name': Store.F_DROID.value,
        'url': 'https://f-droid.org/repository/browse/?fdid=com'
               '.github.dfa.diaspora_android ',
        'fully_qualified_name': 'com.github.dfa.diaspora_android'
    }]
}, {
    'name':
        _('diaspora*'),
    'platforms': [{
        'type':
            'web',
        'url':
            format_lazy('https://diaspora.{host}',
                        host=get_configured_domain_name())
    }]
}]
