import cherrypy
from django import forms
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
import cfg
import actions
import service
import util


SIDE_MENU = {'title': _('XMPP'),
             'items': [{'url': '/services/xmpp/configure',
                        'text': 'Configure XMPP Server'},
                       {'url': '/services/xmpp/register',
                        'text': 'Register XMPP Account'}]}


class XMPP(PagePlugin):
    """XMPP Page"""
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page('services.xmpp')
        cfg.html_root.services.menu.add_item('XMPP', 'icon-comment',
                                             '/services/xmpp', 40)

        self.client_service = service.Service(
            'xmpp-client', _('Chat Server - client connections'),
            is_external=True, enabled=True)
        self.server_service = service.Service(
            'xmpp-server', _('Chat Server - server connections'),
            is_external=True, enabled=True)
        self.bosh_service = service.Service(
            'xmpp-bosh', _('Chat Server - web interface'), is_external=True,
            enabled=True)

    @staticmethod
    @cherrypy.expose
    @require()
    def index(**kwargs):
        """Serve XMPP page"""
        del kwargs  # Unused
        main = "<p>XMPP Server Accounts and Configuration</p>"

        sidebar_right = util.render_template(template='menu_block',
                                             menu=SIDE_MENU)
        return util.render_template(title="XMPP Server", main=main,
                                    sidebar_right=sidebar_right)


class ConfigureForm(forms.Form):  # pylint: disable-msg=W0232
    """Configuration form"""
    inband_enabled = forms.BooleanField(
        label=_('Allow In-Band Registration'), required=False,
        help_text=_('When enabled, anyone who can reach this server will be \
allowed to register an account through an XMPP client'))

    # XXX: Only present due to issue with submitting empty form
    dummy = forms.CharField(label='Dummy', initial='dummy',
                            widget=forms.HiddenInput())


class Configure(PagePlugin):
    """Configuration page"""

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("services.xmpp.configure")

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the configuration form"""
        status = self.get_status()

        form = None
        messages = []

        if kwargs:
            form = ConfigureForm(kwargs, prefix='xmpp')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._apply_changes(status, form.cleaned_data, messages)
                status = self.get_status()
                form = ConfigureForm(initial=status, prefix='xmpp')
        else:
            form = ConfigureForm(initial=status, prefix='xmpp')

        sidebar_right = util.render_template(template='menu_block',
                                             menu=SIDE_MENU)
        return util.render_template(template='xmpp_configure',
                                    title=_('Configure XMPP Server'),
                                    form=form, messages=messages,
                                    sidebar_right=sidebar_right)

    @staticmethod
    def get_status():
        """Return the current status"""
        output, error = actions.run('xmpp-setup', 'status')
        if error:
            raise Exception('Error getting status: %s' % error)

        return {'inband_enabled': 'inband_enable' in output.split()}

    @staticmethod
    def sidebar_right(**kwargs):
        """Return rendered string for sidebar on the right"""
        del kwargs  # Unused

        return util.render_template(template='menu_block', menu=SIDE_MENU)

    @staticmethod
    def _apply_changes(old_status, new_status, messages):
        """Apply the form changes"""
        cfg.log.info('Status - %s, %s' % (old_status, new_status))

        if old_status['inband_enabled'] == new_status['inband_enabled']:
            messages.append(('info', _('Setting unchanged')))
            return

        if new_status['inband_enabled']:
            messages.append(('success', _('Inband registration enabled')))
            option = 'inband_enable'
        else:
            messages.append(('success', _('Inband registration disabled')))
            option = 'noinband_enable'

        cfg.log.info('Option - %s' % option)

        _output, error = actions.superuser_run('xmpp-setup', [option])
        del _output
        if error:
            raise Exception('Error running command - %s' % error)


class RegisterForm(forms.Form):  # pylint: disable-msg=W0232
    """Configuration form"""
    username = forms.CharField(label=_('Username'))

    password = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput())


class Register(PagePlugin):
    """User registration page"""

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page('services.xmpp.register')

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve the registration form"""
        form = None
        messages = []

        if kwargs:
            form = RegisterForm(kwargs, prefix='xmpp')
            # pylint: disable-msg=E1101
            if form.is_valid():
                self._register_user(form.cleaned_data, messages)
                form = RegisterForm(prefix='xmpp')
        else:
            form = RegisterForm(prefix='xmpp')

        sidebar_right = util.render_template(template='menu_block',
                                             menu=SIDE_MENU)
        return util.render_template(template='xmpp_register',
                                    title=_('Register XMPP Account'),
                                    form=form, messages=messages,
                                    sidebar_right=sidebar_right)

    @staticmethod
    def _register_user(data, messages):
        """Register a new XMPP user"""
        output, error = actions.superuser_run(
            'xmpp-register', [data['username'], data['password']])
        if error:
            raise Exception('Error registering user - %s' % error)

        if 'successfully registered' in output:
            messages.append(('success',
                             _('Registered account for %s' %
                               data['username'])))
        else:
            messages.append(('error',
                             _('Failed to register account for %s: %s') %
                             (data['username'], output)))
