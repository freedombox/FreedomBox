from django import forms
from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _

import actions
import cfg
from ..lib.auth import login_required


def get_modules_available():
    """Return list of all modules"""
    output, error = actions.run('module-manager', ['list-available'])
    if error:
        raise Exception('Error getting modules: %s' % error)

    return output.split()


def get_modules_enabled():
    """Return list of all modules"""
    output, error = actions.run('module-manager', ['list-enabled'])
    if error:
        raise Exception('Error getting enabled modules - %s' % error)

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
    menu = cfg.main_menu.find('/sys')
    menu.add_item('Package Manager', 'icon-gift', '/sys/packages', 20)


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
    for field, enabled in new_status.items():
        if not field.endswith('_enabled'):
            continue

        if old_status[field] == new_status[field]:
            continue

        module = field.split('_enabled')[0]
        if enabled:
            output, error = actions.superuser_run(
                'module-manager', ['enable', cfg.python_root, module])
            del output  # Unused

            # TODO: need to get plinth to load the module we just
            # enabled
            if error:
                messages.error(
                    request, _('Error enabling module - {module}').format(
                        module=module))
            else:
                messages.success(
                    request, _('Module enabled - {module}').format(
                        module=module))
        else:
            output, error = actions.superuser_run(
                'module-manager', ['disable', cfg.python_root, module])
            del output  # Unused

            # TODO: need a smoother way for plinth to unload the
            # module
            if error:
                messages.error(
                    request, _('Error disabling module - {module}').format(
                        module=module))
            else:
                messages.success(
                    request, _('Module disabled - {module}').format(
                        module=module))
