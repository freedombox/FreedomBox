from plinth import actions
from plinth.modules import dashboard
from .firewall import get_enabled_status


def enable():
    return actions.superuser_run('firewall', ['set-status', 'enable'])


def disable():
    return actions.superuser_run('firewall', ['set-status', 'disable'])


dashboard.register_app(name='firewall', is_enabled=get_enabled_status,
                       enable=enable, disable=disable,
                       description='Firewall for your Freedombox')
