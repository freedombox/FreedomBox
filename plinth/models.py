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
Django models for the main application
"""

import json

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver


class KVStore(models.Model):
    """Model to store retrieve key/value configuration"""
    key = models.TextField(primary_key=True)
    value_json = models.TextField()

    @property
    def value(self):
        """Return the JSON decoded value of the key/value pair"""
        return json.loads(self.value_json)

    @value.setter
    def value(self, val):
        """Store the value of the key/value pair by JSON encoding it"""
        self.value_json = json.dumps(val)


class Module(models.Model):
    """Model to store current setup versions of a module."""
    name = models.TextField(primary_key=True)
    setup_version = models.IntegerField()


class UserProfile(models.Model):
    """Model to store user profile details that are not auth related."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)

    language = models.CharField(max_length=32, null=True, default=None)


@receiver(models.signals.post_save, sender=User)
def _on_user_post_save(sender, instance, **kwargs):
    """When the user model is saved, user profile too."""
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        UserProfile.objects.update_or_create(user=instance)
