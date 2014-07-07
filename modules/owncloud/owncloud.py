from django import forms
from django.template.response import TemplateResponse
from gettext import gettext as _

import actions
import cfg
from ..lib.auth import login_required
import service


SERVICE = None


class OwnCloudForm(forms.Form):  # pylint: disable-msg=W0232
    """ownCloud configuration form"""
    enabled = forms.BooleanField(label=_('Enable ownCloud'), required=False)


def init():
    """Initialize the ownCloud module"""
    menu = cfg.main_menu.find('/apps')
    menu.add_item('Owncloud', 'icon-picture', '/apps/owncloud', 35)

    status = get_status()

    global SERVICE  # pylint: disable-msg=W0603
    SERVICE = service.Service('owncloud', _('ownCloud'), ['http', 'https'],
                              is_external=True, enabled=status['enabled'])


@login_required
def index(request):
    """Serve the ownCloud configuration page"""
    status = get_status()

    form = None
    messages = []

    if request.method == 'POST':
        form = OwnCloudForm(request.POST, prefix='owncloud')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(status, form.cleaned_data, messages)
            status = get_status()
            form = OwnCloudForm(initial=status, prefix='owncloud')
    else:
        form = OwnCloudForm(initial=status, prefix='owncloud')

    return TemplateResponse(request, 'owncloud.html',
                            {'title': _('ownCloud'),
                             'form': form,
                             'messages_': messages})


def get_status():
    """Return the current status"""
    output, error = actions.run('owncloud-setup', 'status')
    if error:
        raise Exception('Error getting ownCloud status: %s' % error)

    return {'enabled': 'enable' in output.split()}


def _apply_changes(old_status, new_status, messages):
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
    SERVICE.notify_enabled(None, new_status['enabled'])
