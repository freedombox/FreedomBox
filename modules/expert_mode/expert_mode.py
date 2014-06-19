import cherrypy
from django import forms
from gettext import gettext as _
from ..lib.auth import require
from plugin_mount import PagePlugin
import cfg
import util


class ExpertsForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to configure expert mode"""

    expert_mode = forms.BooleanField(
        label=_('Expert Mode'), required=False)

    # XXX: Only present due to issue with submitting empty form
    dummy = forms.CharField(label='Dummy', initial='dummy',
                            widget=forms.HiddenInput())


class Experts(PagePlugin):
    """Expert forms page"""
    order = 60

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page('sys.expert')

        cfg.html_root.sys.menu.add_item(_('Expert Mode'), 'icon-cog',
                                        '/sys/expert', 10)

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the configuration form"""
        status = self.get_status()

        cfg.log.info('Args - %s' % kwargs)

        form = None
        messages = []

        if kwargs:
            form = ExpertsForm(kwargs, prefix='experts')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(form.cleaned_data, messages)
                status = self.get_status()
                form = ExpertsForm(initial=status, prefix='experts')
        else:
            form = ExpertsForm(initial=status, prefix='experts')

        return util.render_template(template='expert_mode',
                                    title=_('Expert Mode'), form=form,
                                    messages=messages)

    @staticmethod
    def get_status():
        """Return the current status"""
        return {'expert_mode': cfg.users.expert()}

    @staticmethod
    def _apply_changes(new_status, messages):
        """Apply expert mode configuration"""
        message = ('info', _('Settings unchanged'))

        user = cfg.users.current()

        if new_status['expert_mode']:
            if not 'expert' in user['groups']:
                user['groups'].append('expert')
                message = ('success', _('Expert mode enabled'))
        else:
            if 'expert' in user['groups']:
                user['groups'].remove('expert')
                message = ('success', _('Expert mode disabled'))

        cfg.users.set(user['username'], user)
        messages.append(message)
