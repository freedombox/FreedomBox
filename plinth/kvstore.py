# SPDX-License-Identifier: AGPL-3.0-or-later
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
