from plinth import actions
from plinth.modules import vault

from .owncloud import get_status

vault.register_app('owncloud', url='/owncloud')


def enable():
    actions.superuser_run('owncloud-setup', ['enable'], async=True)


def disable():
    actions.superuser_run('owncloud-setup', ['noenable'], async=True)


def is_enabled():
    return get_status()['enabled']


vault.register_service('owncloud', enable=enable, disable=disable, 
                       is_enabled=is_enabled)
