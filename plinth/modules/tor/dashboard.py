from plinth import actions
from plinth.modules import dashboard


def enable():
    return actions.superuser_run('tor', ['start'])


def disable():
    return actions.superuser_run('tor', ['stop'])


def is_running():
    return actions.superuser_run("tor", ["is-running"]).strip() == "yes"


dashboard.register_app(name='tor', is_enabled=is_running,
                       enable=enable, disable=disable, synchronous=True,
                       description='Tor anonymization service')
