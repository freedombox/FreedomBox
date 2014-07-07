from django import forms
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from gettext import gettext as _

import actions
import cfg
from ..lib.auth import login_required
import service


SIDE_MENU = {'title': _('XMPP'),
             'items': [{'url': '/apps/xmpp/configure',
                        'text': 'Configure XMPP Server'},
                       {'url': '/apps/xmpp/register',
                        'text': 'Register XMPP Account'}]}


def init():
    """Initialize the XMPP module"""
    menu = cfg.main_menu.find('/apps')
    menu.add_item('Chat', 'icon-comment', '/../jwchat', 20)
    menu.add_item('XMPP', 'icon-comment', '/apps/xmpp', 40)

    service.Service(
        'xmpp-client', _('Chat Server - client connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-server', _('Chat Server - server connections'),
        is_external=True, enabled=True)
    service.Service(
        'xmpp-bosh', _('Chat Server - web interface'), is_external=True,
        enabled=True)


@login_required
def index(request):
    """Serve XMPP page"""
    main = "<p>XMPP Server Accounts and Configuration</p>"

    sidebar_right = render_to_string('menu_block.html', {'menu': SIDE_MENU},
                                     RequestContext(request))

    return TemplateResponse(request, 'login_nav.html',
                            {'title': _('XMPP Server'),
                             'main': main,
                             'sidebar_right': sidebar_right})


class ConfigureForm(forms.Form):  # pylint: disable-msg=W0232
    """Configuration form"""
    inband_enabled = forms.BooleanField(
        label=_('Allow In-Band Registration'), required=False,
        help_text=_('When enabled, anyone who can reach this server will be \
allowed to register an account through an XMPP client'))


@login_required
def configure(request):
    """Serve the configuration form"""
    status = get_status()

    form = None
    messages = []

    if request.method == 'POST':
        form = ConfigureForm(request.POST, prefix='xmpp')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(status, form.cleaned_data, messages)
            status = get_status()
            form = ConfigureForm(initial=status, prefix='xmpp')
    else:
        form = ConfigureForm(initial=status, prefix='xmpp')

    sidebar_right = render_to_string('menu_block.html', {'menu': SIDE_MENU},
                                     RequestContext(request))

    return TemplateResponse(request, 'xmpp_configure.html',
                            {'title': _('Configure XMPP Server'),
                             'form': form,
                             'messages_': messages,
                             'sidebar_right': sidebar_right})


def get_status():
    """Return the current status"""
    output, error = actions.run('xmpp-setup', 'status')
    if error:
        raise Exception('Error getting status: %s' % error)

    return {'inband_enabled': 'inband_enable' in output.split()}


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
    del _output  # Unused
    if error:
        raise Exception('Error running command - %s' % error)


class RegisterForm(forms.Form):  # pylint: disable-msg=W0232
    """Configuration form"""
    username = forms.CharField(label=_('Username'))

    password = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput())


@login_required
def register(request):
    """Serve the registration form"""
    form = None
    messages = []

    if request.method == 'POST':
        form = RegisterForm(request.POST, prefix='xmpp')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _register_user(form.cleaned_data, messages)
            form = RegisterForm(prefix='xmpp')
    else:
        form = RegisterForm(prefix='xmpp')

    sidebar_right = render_to_string('menu_block.html', {'menu': SIDE_MENU},
                                     RequestContext(request))

    return TemplateResponse(request, 'xmpp_register.html',
                            {'title': _('Register XMPP Account'),
                             'form': form,
                             'messages_': messages,
                             'sidebar_right': sidebar_right})


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
