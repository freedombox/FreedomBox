# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django migration for renaming all the DB tables from plinth_ to freedombox_.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('freedombox', '0006_userpasskey'),
    ]

    operations = [
        migrations.AlterModelTable(name='KVStore', table='freedombox_kvstore'),
        migrations.AlterModelTable(name='Module', table='freedombox_module'),
        migrations.AlterModelTable(name='UserProfile',
                                   table='freedombox_userprofile'),
        migrations.AlterModelTable(name='StoredNotification',
                                   table='freedombox_storednotification'),
        migrations.AlterModelTable(name='UserPasskey',
                                   table='freedombox_userpasskey'),
    ]
