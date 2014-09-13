import importlib
from collections import OrderedDict
from django.dispatch import receiver

from plinth import module_loader, errors
from plinth.signals import post_module_loading

apps = OrderedDict()
services = OrderedDict()
statusline_items = OrderedDict()


def register_app(name, **kwargs):
    apps[name] = dict(**kwargs)


def register_service(name, **kwargs):
    """ Convention about what a service looks like:
    - name: name of the app, exactly as in the module folder
    - functions: is_enabled, enable, disable
    """
    for param in ['is_enabled', 'enable', 'disable']:
        if param not in kwargs:
            raise errors.PlinthError('Missing parameter for module %s: %s' %
                                     (name, param))
    services[name] = dict(**kwargs)


def register_statusline(name, **kwargs):
    statusline_items[name] = dict(**kwargs)


@receiver(post_module_loading)
def import_vault_files(sender, **kwargs):
    """Try to import a 'vault.py' python module from each of our own modules

    There's nothing wrong with a module not having a 'vault.py' file, and
    calling vault.register_app somewhere else.
    Right now that's just a way to keep the vault module separated.
    We might remove this and just use the <module>.init() function.
    """
    for modulename in sorted(module_loader.LOADED_MODULES):
        path = "plinth.modules.%s.vault" % modulename
        try:
            importlib.import_module(path)
        except ImportError:
            pass
