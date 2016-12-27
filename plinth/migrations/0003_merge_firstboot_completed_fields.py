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
Remove the deprecated KVStore entries 'setup_state' and 'firstboot_state',
and only use the new entry 'firstboot_completed' instead.
"""

from __future__ import unicode_literals

from django.db import migrations
from plinth.models import KVStore


def merge_firstboot_finished_fields(apps, schema_editor):
    """
    Merge 'setup_state' and 'firstboot_state' into 'firstboot_completed'.

    'firstboot_completed' is the most accurate name for now, and by combining
    the fields we do not have to deal with legacy states/fields anymore.
    """
    # Get and remove 'firstboot_state'
    firstboot_state = 0
    try:
        _object = KVStore.objects.get(key='firstboot_state')
    except KVStore.DoesNotExist:
        pass
    else:
        firstboot_state = _object.value
        _object.delete()

    # Get and remove 'setup_state'
    setup_state = 0
    try:
        _object = KVStore.objects.get(key='setup_state')
    except KVStore.DoesNotExist:
        pass
    else:
        setup_state = _object.value
        _object.delete()

    # Get current 'firstboot_completed'
    firstboot_completed = False
    try:
        _object = KVStore.objects.get(key='firstboot_completed')
    except KVStore.DoesNotExist:
        pass
    else:
        firstboot_completed = _object.value

    # Set new 'firstboot_completed' if needed
    new_firstboot_completed = bool(firstboot_completed or setup_state or
                                   firstboot_state)
    if new_firstboot_completed and not firstboot_completed:
        obj, created = KVStore.objects.get_or_create(key='firstboot_completed')
        obj.value = 1
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('plinth', '0002_modulestore'),
    ]

    operations = [
        migrations.RunPython(merge_firstboot_finished_fields),
    ]
