import importlib
from collections import OrderedDict
from django.dispatch import receiver

from plinth import module_loader, errors
from plinth.signals import post_module_loading

apps = OrderedDict()
services = OrderedDict()
statusline_items = OrderedDict()


def _check_params(given_params, required_params):
    """Check whether all required paramters are given. Raises a PlinthError
    otherwise.

    - given_params: given parameter dict (**kwargs)
    - required_params: iterable with parameter-names
    """
    for param in required_params:
        if param not in given_params:
            raise errors.PlinthError('Missing parameter: %s' % param)


def register_app(template='vault_app_default.inc', **kwargs):
    _check_params(kwargs, ['name'])
    if 'template' not in kwargs:
        kwargs['template'] = template
    apps[kwargs['name']] = dict(**kwargs)


def register_service(template='vault_service_default.inc', synchronous=False,
                     **kwargs):
    """ Convention about what a service looks like:
    - name: name of the app, exactly as in the module folder
    - functions: is_enabled, enable, disable
    Optional parameters:
    - template: template to use for rendering the service-item
    - synchronous: whether the enable/disable procedure is synchronous.
      Otherwise we'll inform the user that the changes can take some time.
    """
    _check_params(kwargs, ['name', 'is_enabled', 'enable', 'disable'])
    if 'template' not in kwargs:
        kwargs['template'] = template
        kwargs['synchronous'] = synchronous
    services[kwargs['name']] = dict(**kwargs)


def register_statusline(**kwargs):
    _check_params(kwargs, ['name', 'template'])
    statusline_items[kwargs['name']] = dict(**kwargs)


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
