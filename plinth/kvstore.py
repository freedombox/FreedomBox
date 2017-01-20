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
Simple key/value store using Django models
"""

from plinth.models import KVStore


def get(key):
    """Return the value of a key"""
    # pylint: disable-msg=E1101
    return KVStore.objects.get(pk=key).value


def get_default(key, default_value):
    """Return the value of the key if key exists else return default_value"""
    try:
        return get(key)
    except Exception:
        return default_value


def set(key, value):  # pylint: disable-msg=W0622
    """Store the value of a key"""
    store = KVStore(key=key, value=value)
    store.save()


def delete(key):
    """Delete a key"""
    return KVStore.objects.get(key=key).delete()
