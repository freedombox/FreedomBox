# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django models for the main application
"""

import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver

from . import db


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
    with db.lock:
        if hasattr(instance, 'userprofile'):
            instance.userprofile.save()
        else:
            UserProfile.objects.update_or_create(user=instance)


class JSONField(models.TextField):
    """Store and retrieve JSON data into a TextField."""

    def to_python(self, value):
        """Deserialize a text string from form field to Python dict."""
        if not value:
            return self.default()

        try:
            return json.loads(value)
        except json.decoder.JSONDecodeError:
            raise ValidationError('Invalid JSON value')

    def from_db_value(self, value, *args, **kwargs):
        """Deserialize a value from DB to Python dict."""
        return self.to_python(value)

    def get_prep_value(self, value):
        """Serialize the Python dict to text for form field."""
        return json.dumps(value or self.default())


class StoredNotification(models.Model):
    """Model to store a user notification."""
    id = models.CharField(primary_key=True, max_length=128)
    app_id = models.CharField(max_length=128, null=True, default=None)
    severity = models.CharField(max_length=32)
    title = models.CharField(max_length=256)
    message = models.TextField(null=True, default=None)
    actions = JSONField(default=list)
    body_template = models.CharField(max_length=128, null=True, default=None)
    data = JSONField(default=dict)
    created_time = models.DateTimeField(auto_now_add=True)
    last_update_time = models.DateTimeField(auto_now=True)
    user = models.CharField(max_length=128, null=True, default=None)
    group = models.CharField(max_length=128, null=True, default=None)
    dismissed = models.BooleanField(default=False)
