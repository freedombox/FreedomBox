from plinth import actions
from plinth.modules import vault


def enable():
    return actions.superuser_run('tor', ['start'])


def disable():
    return actions.superuser_run('tor', ['stop'])


def is_running():
    return actions.superuser_run("tor", ["is-running"]).strip() == "yes"


vault.register_service(name='tor', is_enabled=is_running,
                       enable=enable, disable=disable, synchronous=True,
                       description='Tor anonymization service')
