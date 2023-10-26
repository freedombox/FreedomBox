# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Simple key/value store using Django models
"""

from . import db


def get(key):
    """Return the value of a key"""
    from plinth.models import KVStore

    with db.lock:
        # pylint: disable-msg=E1101
        return KVStore.objects.get(pk=key).value


def get_default(key, default_value):
    """Return the value of the key if key exists else return default_value"""
    with db.lock:
        try:
            return get(key)
        except Exception:
            return default_value


def set(key, value):  # pylint: disable-msg=W0622
    """Store the value of a key"""
    from plinth.models import KVStore
    with db.lock:
        store = KVStore(key=key, value=value)
        store.save()


def delete(key, ignore_missing=False):
    """Delete a key"""
    from plinth.models import KVStore
    with db.lock:
        try:
            return KVStore.objects.get(key=key).delete()
        except KVStore.DoesNotExist:
            if not ignore_missing:
                raise
