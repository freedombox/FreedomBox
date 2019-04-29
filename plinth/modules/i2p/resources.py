#
# This file is part of FreedomBox.
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
"""
Pre-defined list of favorites for I2P and some additional favorites.
"""

DEFAULT_FAVORITES = [
    {
        'name': 'anoncoin.i2p',
        'description': 'The Anoncoin project',
        'icon': '/themes/console/images/anoncoin_32.png',
        'url': 'http://anoncoin.i2p/'
    },
    {
        'name': 'Dev Builds',
        'description': 'Development builds of I2P',
        'icon': '/themes/console/images/script_gear.png',
        'url': 'http://bobthebuilder.i2p/'
    },
    {
        'name': 'Dev Forum',
        'description': 'Development forum',
        'icon': '/themes/console/images/group_gear.png',
        'url': 'http://zzz.i2p/'
    },
    {
        'name': 'echelon.i2p',
        'description': 'I2P Applications',
        'icon': '/themes/console/images/box_open.png',
        'url': 'http://echelon.i2p/'
    },
    {
        'name': 'exchanged.i2p',
        'description': 'Anonymous cryptocurrency exchange',
        'icon': '/themes/console/images/exchanged.png',
        'url': 'http://exchanged.i2p/'
    },
    {
        'name': 'I2P Bug Reports',
        'description': 'Bug tracker',
        'icon': '/themes/console/images/bug.png',
        'url': 'http://trac.i2p2.i2p/report/1'
    },
    {
        'name': 'I2P FAQ',
        'description': 'Frequently Asked Questions',
        'icon': '/themes/console/images/question.png',
        'url': 'http://i2p-projekt.i2p/faq'
    },
    {
        'name': 'I2P Forum',
        'description': 'Community forum',
        'icon': '/themes/console/images/group.png',
        'url': 'http://i2pforum.i2p/'
    },
    {
        'name': 'I2P Plugins',
        'description': 'Add-on directory',
        'icon': '/themes/console/images/info/plugin_link.png',
        'url': 'http://i2pwiki.i2p/index.php?title=Plugins'
    },
    {
        'name': 'I2P Technical Docs',
        'description': 'Technical documentation',
        'icon': '/themes/console/images/education.png',
        'url': 'http://i2p-projekt.i2p/how'
    },
    {
        'name': 'I2P Wiki',
        'description': 'Anonymous wiki - share the knowledge',
        'icon': '/themes/console/images/i2pwiki_logo.png',
        'url': 'http://i2pwiki.i2p/'
    },
    {
        'name': 'Planet I2P',
        'description': 'I2P News',
        'icon': '/themes/console/images/world.png',
        'url': 'http://planet.i2p/'
    },
    {
        'name': 'PrivateBin',
        'description': 'Encrypted I2P Pastebin',
        'icon': '/themes/console/images/paste_plain.png',
        'url': 'http://paste.crypthost.i2p/'
    },
    {
        'name': 'Project Website',
        'description': 'I2P home page',
        'icon': '/themes/console/images/info_rhombus.png',
        'url': 'http://i2p-projekt.i2p/'
    },
    {
        'name': 'stats.i2p',
        'description': 'I2P Network Statistics',
        'icon': '/themes/console/images/chart_line.png',
        'url': 'http://stats.i2p/cgi-bin/dashboard.cgi'
    },
    {
        'name': 'The Tin Hat',
        'description': 'Privacy guides and tutorials',
        'icon': '/themes/console/images/thetinhat.png',
        'url': 'http://secure.thetinhat.i2p/'
    },
    {
        'name': 'Trac Wiki',
        'description': '',
        'icon': '/themes/console/images/billiard_marker.png',
        'url': 'http://trac.i2p2.i2p/'
    }
]
ADDITIONAL_FAVORITES = [
    {
        'name': 'Searx instance',
        'url': 'http://ransack.i2p'
    },
    {
        'name': 'Torrent tracker',
        'url': 'http://tracker2.postman.i2p'
    },
    {
        'name': 'YaCy Legwork',
        'url': 'http://legwork.i2p'
    },
    {
        'name': 'YaCy Seeker',
        'url': 'http://seeker.i2p'
    },
]

FAVORITES = DEFAULT_FAVORITES + ADDITIONAL_FAVORITES
