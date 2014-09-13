from plinth import actions
from plinth.modules import vault
from .firewall import get_enabled_status


def enable():
    return actions.superuser_run('firewall', ['set-status', 'enable'])


def disable():
    return actions.superuser_run('firewall', ['set-status', 'disable'])


vault.register_service('firewall', is_enabled=get_enabled_status,
                       enable=enable, disable=disable)
