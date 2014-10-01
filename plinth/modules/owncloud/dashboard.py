from plinth import actions
from plinth.modules import dashboard

from .owncloud import get_status


#dashboard.register_app(name='owncloud', url='/owncloud',
#                   description='Cloud services running on your Freedombox')


def enable():
    actions.superuser_run('owncloud-setup', ['enable'], async=True)


def disable():
    actions.superuser_run('owncloud-setup', ['noenable'], async=True)


def is_enabled():
    return get_status()['enabled']


dashboard.register_app(name='owncloud', enable=enable, disable=disable,
                       is_enabled=is_enabled, url='/owncloud',
                       template='dashboard_owncloud.inc',
                       description='Cloud services running on your Freedombox')
