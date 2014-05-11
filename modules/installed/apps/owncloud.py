import cherrypy
from django import forms
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
import actions
import cfg
import service
import util


class OwnCloudForm(forms.Form):  # pylint: disable-msg=W0232
    """ownCloud configuration form"""
    enabled = forms.BooleanField(label=_('Enable ownCloud'), required=False)

    # XXX: Only present due to issue with submitting empty form
    dummy = forms.CharField(label='Dummy', initial='dummy',
                            widget=forms.HiddenInput())


class OwnCloud(PagePlugin):
    """ownCloud configuration page"""
    order = 90

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page('apps.owncloud')

        cfg.html_root.apps.menu.add_item('Owncloud', 'icon-picture',
                                         '/apps/owncloud', 35)

        status = self.get_status()
        self.service = service.Service('owncloud', _('ownCloud'),
                                       ['http', 'https'], is_external=True,
                                       enabled=status['enabled'])

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the ownCloud configuration page"""
        status = self.get_status()

        form = None
        messages = []

        if kwargs:
            form = OwnCloudForm(kwargs, prefix='owncloud')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(status, form.cleaned_data, messages)
                status = self.get_status()
                form = OwnCloudForm(initial=status, prefix='owncloud')
        else:
            form = OwnCloudForm(initial=status, prefix='owncloud')

        return util.render_template(template='owncloud', title=_('ownCloud'),
                                    form=form, messages=messages)

    @staticmethod
    def get_status():
        """Return the current status"""
        output, error = actions.run('owncloud-setup', 'status')
        if error:
            raise Exception('Error getting ownCloud status: %s' % error)

        return {'enabled': 'enable' in output.split()}

    def _apply_changes(self, old_status, new_status, messages):
        """Apply the changes"""
        if old_status['enabled'] == new_status['enabled']:
            messages.append(('info', _('Setting unchanged')))
            return

        if new_status['enabled']:
            messages.append(('success', _('ownCloud enabled')))
            option = 'enable'
        else:
            messages.append(('success', _('ownCloud disabled')))
            option = 'noenable'

        actions.superuser_run('owncloud-setup', [option], async=True)

        # Send a signal to other modules that the service is
        # enabled/disabled
        self.service.notify_enabled(self, new_status['enabled'])
