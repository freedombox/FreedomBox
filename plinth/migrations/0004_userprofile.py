# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-01-29 10:21
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.contrib.auth.models import User
from django.db import migrations, models

from plinth.models import UserProfile


def insert_users(apps, schema_editor):
    """For each user, create their empty profiles."""
    for user in User.objects.all():
        UserProfile(user=user).save()


def truncate_user_profile(apps, schema_editor):
    """Delete all user profiles."""
    UserProfile.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plinth', '0003_merge_firstboot_completed_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id',
                 models.AutoField(auto_created=True, primary_key=True,
                                  serialize=False, verbose_name='ID')),
                ('language',
                 models.CharField(default=None, max_length=32, null=True)),
                ('user',
                 models.OneToOneField(
                     on_delete=django.db.models.deletion.CASCADE,
                     to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(code=insert_users,
                             reverse_code=truncate_user_profile),
    ]
