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

from django.contrib.auth.models import Group, User


def add_user(username, passphrase, name='', email='', expert=False):
    """Add a new user with specified username and passphrase"""
    if not username:
        return 'Must specify a username!'

    if not passphrase:
        return 'Must specify a passphrase!'

    user = User.objects.create_user(username, email=email,
                                    password=passphrase)
    user.first_name = name
    user.save()

    if expert:
        user.groups.add(get_or_create_group('Expert'))


def get_or_create_group(name):
    """Return an existing or newly created group with given name"""
    try:
        group = Group.objects.get(name__exact=name)
    except Group.DoesNotExist:
        group = Group(name=name)
        group.save()

    return group
