# SPDX-License-Identifier: AGPL-3.0-or-later
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
    new_firstboot_completed = bool(firstboot_completed or setup_state
                                   or firstboot_state)
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
