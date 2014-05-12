import cherrypy
from django import forms
from gettext import gettext as _
from auth import require
from plugin_mount import PagePlugin
import actions
import cfg
import util


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
    # XXX: Only present due to issue with submitting empty form
    dummy = forms.CharField(label='Dummy', initial='dummy',
                            widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=E1002, E1101
        super(forms.Form, self).__init__(*args, **kwargs)

        modules_available = get_modules_available()

        for module in modules_available:
            label = _('Enable {module}').format(module=module)
            self.fields[module + '_enabled'] = forms.BooleanField(
                label=label, required=False)


class Packages(PagePlugin):
    """Package page"""
    order = 20

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page('sys.packages')

        cfg.html_root.sys.menu.add_item('Package Manager', 'icon-gift',
                                        '/sys/packages', 20)

    @cherrypy.expose
    @require()
    def index(self, *args, **kwargs):
        """Serve the form"""
        del args  # Unused

        status = self.get_status()

        form = None
        messages = []

        if kwargs:
            form = PackagesForm(kwargs, prefix='packages')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(status, form.cleaned_data, messages)
                status = self.get_status()
                form = PackagesForm(initial=status, prefix='packages')
        else:
            form = PackagesForm(initial=status, prefix='packages')

        return util.render_template(template='packages',
                                    title=_('Add/Remove Plugins'),
                                    form=form, messages=messages)

    @staticmethod
    def get_status():
        """Return the current status"""
        modules_available = get_modules_available()
        modules_enabled = get_modules_enabled()

        return {module + '_enabled': module in modules_enabled
                for module in modules_available}

    @staticmethod
    def _apply_changes(old_status, new_status, messages):
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
                    messages.append(
                        ('error', _('Error enabling module - {module}').format(
                         module=module)))
                else:
                    messages.append(
                        ('success', _('Module enabled - {module}').format(
                         module=module)))
            else:
                output, error = actions.superuser_run(
                    'module-manager', ['disable', cfg.python_root, module])
                del output  # Unused

                # TODO: need a smoother way for plinth to unload the
                # module
                if error:
                    messages.append(
                        ('error',
                         _('Error disabling module - {module}').format(
                             module=module)))
                else:
                    messages.append(
                        ('success', _('Module disabled - {module}').format(
                         module=module)))
