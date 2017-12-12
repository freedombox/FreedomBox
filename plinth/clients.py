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
"""
Utility methods for providing client information.
"""

from django.utils.functional import Promise
from enum import Enum


class Desktop_OS(Enum):
    GNU_LINUX = 'gnu-linux'
    MAC_OS = 'macos'
    WINDOWS = 'windows'


class Mobile_OS(Enum):
    ANDROID = 'android'
    IOS = 'ios'


class Store(Enum):
    APP_STORE = 'app-store'
    F_DROID = 'f-droid'
    GOOGLE_PLAY = 'google-play'


class Package(Enum):
    DEB = 'deb'
    HOMEBREW = 'brew'
    RPM = 'rpm'


def enum_values(enum):
    return [option.value for option in list(enum)]


def _check(client, condition):
    """Check if any of a list of clients satisfies the given condition"""
    return any(platform for platform in client['platforms']
               if condition(platform))


def _client_has_desktop(client):
    """Filter to find out whether an application has desktop clients"""
    return _check(
        client, lambda platform: platform.get('os') in enum_values(Desktop_OS))


def _client_has_mobile(client):
    """Filter to find out whether an application has mobile clients"""
    return _check(
        client, lambda platform: platform.get('os') in enum_values(Mobile_OS))


def _client_has_web(client):
    """Filter to find out whether an application has web clients"""
    return _check(client, lambda platform: platform['type'] == 'web')


def _client_has_package(client):
    """Filter to find out whether an application has web clients"""
    return _check(client, lambda platform: platform['type'] == 'package')


def of_type(clients, client_type):
    """Filter and get clients of a particular type"""
    filters = {
        'mobile': _client_has_mobile,
        'desktop': _client_has_desktop,
        'web': _client_has_web,
        'package': _client_has_package,
    }
    return list(filter(filters[client_type], clients))


def store_url(store, package_id):
    """Return a full App store URL given package id and type of store."""
    stores = {
        'google-play': 'https://play.google.com/store/apps/details?id={}',
        'f-droid': 'https://f-droid.org/packages/{}'
    }
    return stores[store].format(package_id)


def validate(clients):
    """Validate the clients' information schema."""
    assert isinstance(clients, list)
    for client in clients:
        _validate_client(client)

    return clients


def _validate_client(client):
    """Validate a single client's information schema."""
    assert isinstance(client, dict)
    assert 'name' in client
    assert isinstance(client['platforms'], list)
    for platform in client['platforms']:
        _validate_platform(platform)


def _validate_platform(platform):
    """Validate a single platform's schema."""
    assert platform['type'] in ('package', 'download', 'store', 'web')
    validate_method = globals()['_validate_platform_' + platform['type']]
    validate_method(platform)


def _validate_platform_package(platform):
    """Validate a platform of type package."""
    assert platform['format'] in enum_values(Package)
    assert isinstance(platform['name'], (str, Promise))


def _validate_platform_download(platform):
    """Validate a platform of type download."""
    assert platform['os'] in enum_values(Desktop_OS)
    assert isinstance(platform['url'], (str, Promise))


def _validate_platform_store(platform):
    """Validate a platform of type store."""
    assert platform['os'] in enum_values(Mobile_OS)
    assert platform['store_name'] in enum_values(Store)
    assert isinstance(platform['url'], (str, Promise))


def _validate_platform_web(platform):
    """Validate a platform of type web."""
    assert isinstance(platform['url'], (str, Promise))
