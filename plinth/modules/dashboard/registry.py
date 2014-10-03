#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import importlib
import inspect
from collections import OrderedDict
from django.dispatch import receiver

from plinth import module_loader, errors
from plinth.signals import post_module_loading

apps = OrderedDict()
statusline_items = OrderedDict()


def register_app(name, is_enabled, enable, disable, synchronous=False,
                 template='dashboard_app_default.inc', url=None,
                 description='', additional_params={}):
    """Representation of apps/services installed on the freedombox

    Parameters:
    - name: app/service name to be displayed in the dashboard
    - is_enabled, enable, disable: functions to show/modify app status
    - synchronous: whether the enable/disable procedure is synchronous. If an
      app is not synchronous we tell the user that changes can take some time.
    - template: template to use for rendering the app
    - url: link to the app on the freedombox
    - description: to be displayed in the dashboard
    - additional_args: use these instead of **kwargs to avoid varable name
      conflicts inside this function
    """
    if name in apps:
        msg = 'A module named %s is already registered!' % name
        raise errors.PlinthError(msg)

    _locals = locals()
    functions = set(['is_enabled', 'enable', 'disable'])
    for function in functions:
        if not callable(_locals[function]):
            raise TypeError('parameter %s is expected to be callable')

    arguments = inspect.getargspec(register_app).args
    arguments.remove('additional_params')
    apps[name] = _build_args_dict(arguments, additional_params, _locals)


def register_statusline(name, template, **kwargs):
    _arguments = inspect.getargspec(register_statusline).args
    statusline_items[name] = _build_args_dict(_arguments, kwargs, locals())


def _build_args_dict(args, kwargs, localvars):
    '''Create one dictionary out of args and kwargs using locals()'''
    params = dict(**kwargs)
    for param in args:
        params[param] = localvars[param]
    return params


@receiver(post_module_loading)
def import_dashboard_files(sender, **kwargs):
    """Try to import a 'dashboard.py' python module from each of our own modules

    There's nothing wrong with a module not having a 'dashboard.py' file, and
    calling dashboard.register_app somewhere else.
    Right now that's just a way to keep the dashboard module separated.
    We might remove this and just use the <module>.init() function.
    """
    for modulepath in sorted(module_loader.loaded_modules):
        path = "%s.dashboard" % modulepath
        try:
            importlib.import_module(path)
        except ImportError:
            pass
