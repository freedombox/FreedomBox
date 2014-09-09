from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from gettext import gettext as _
import os

from plinth import actions
from plinth import cfg


def get_modules_available():
    """Return list of all modules"""
    output = actions.run('module-manager', ['list-available'])
    return output.split()


def get_modules_enabled():
    """Return list of all modules"""
    root = os.path.join(os.path.dirname(__file__), '..', '..')
    output = actions.run('module-manager',
                         ['list-enabled', root])
    return output.split()


class PackagesForm(forms.Form):
    """Packages form"""
    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=E1002, E1101
        super(forms.Form, self).__init__(*args, **kwargs)

        modules_available = get_modules_available()

        for module in modules_available:
            label = _('Enable {module}').format(module=module)
            self.fields[module + '_enabled'] = forms.BooleanField(
                label=label, required=False)


def init():
    """Initialize the Packages module"""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname('Package Manager', 'icon-gift', 'packages:index', 20)


@login_required
def index(request):
    """Serve the form"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = PackagesForm(request.POST, prefix='packages')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = PackagesForm(initial=status, prefix='packages')
    else:
        form = PackagesForm(initial=status, prefix='packages')

    return TemplateResponse(request, 'packages.html',
                            {'title': _('Add/Remove Plugins'),
                             'form': form})


def get_status():
    """Return the current status"""
    modules_available = get_modules_available()
    modules_enabled = get_modules_enabled()

    return {module + '_enabled': module in modules_enabled
            for module in modules_available}


def _apply_changes(request, old_status, new_status):
    """Apply form changes"""
    root = os.path.join(os.path.dirname(__file__), '..', '..')
    for field, enabled in new_status.items():
        if not field.endswith('_enabled'):
            continue

        if old_status[field] == new_status[field]:
            continue

        module = field.split('_enabled')[0]
        if enabled:
            try:
                actions.superuser_run('module-manager',
                                      ['enable', root, module])
            except Exception:
                # TODO: need to get plinth to load the module we just
                # enabled
                messages.error(
                    request, _('Error enabling module - {module}').format(
                        module=module))
            else:
                messages.success(
                    request, _('Module enabled - {module}').format(
                        module=module))
        else:
            try:
                actions.superuser_run('module-manager',
                                      ['disable', root, module])
            except Exception:
                # TODO: need a smoother way for plinth to unload the
                # module
                messages.error(
                    request, _('Error disabling module - {module}').format(
                        module=module))
            else:
                messages.success(
                    request, _('Module disabled - {module}').format(
                        module=module))
