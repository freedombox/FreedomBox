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

"""
Views for the tinc module.
"""

import random
import shutil
import socket
import string

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from .forms import TincForm, TincSetupForm
from plinth import actions
from plinth.modules import tinc
from plinth.modules.names import get_domain


def index(request):
    """Serve configuration page."""
    status = get_status()
    if not status['is_setup']:
        return redirect(reverse_lazy('tinc:setup'))

    form = None

    if request.method == 'POST':
        form = TincForm(request.POST, prefix='tinc')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = TincForm(initial=status, prefix='tinc')
    else:
        form = TincForm(initial=status, prefix='tinc')

    return TemplateResponse(request, 'tinc.html',
                            {'title': tinc.title,
                             'description': tinc.description,
                             'status': status,
                             'form': form})


def setup(request):
    """Serve initial configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = TincSetupForm(request.POST, prefix='tinc')
        if form.is_valid():
            _setup(form.cleaned_data)
            return redirect(reverse_lazy('tinc:index'))
    else:
        name = get_domain('domainname') or socket.gethostname()
        # suggest a more random name for common hostnames
        if name == 'freedombox' or name == 'debian':
            name += '_' + ''.join(
                random.choice(
                    string.ascii_letters + string.digits) for x in range(20))
        initial = {
            'name': name,
            'ip': '10.{0}.{1}.{2}'.format(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)),
            'address': get_domain('domainname'),
        }
        form = TincSetupForm(initial=initial, prefix='tinc')

    return TemplateResponse(request, 'tinc_setup.html',
                            {'title': tinc.title,
                             'description': tinc.description,
                             'status': status,
                             'form': form})


@require_POST
def package(request):
    """Provide VPN configuration package for download."""
    package_name = shutil.make_archive(
        'freedombox-tinc-package', 'gztar',
        '/etc/tinc/freedombox', 'hosts')

    with open(package_name, 'rb') as package_file:
        package_string = package_file.read()

    response = HttpResponse(package_string,
                            content_type='application/gzip')
    response['Content-Encoding'] = 'gzip'
    response['Content-Disposition'] = \
        'attachment; filename=freedombox-tinc-package.tar.gz'

    return response


def get_status():
    """Get the current status of tinc."""
    return {'is_setup': tinc.is_setup(),
            'enabled': tinc.service.is_enabled(),
            'is_running': tinc.service.is_running()}


def _setup(data):
    """Setup a tinc VPN."""
    actions.superuser_run(
        'tinc', ['setup', '--name', data['name'], '--ip', data['ip'],
                 '--address', data['address']])


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        if new_status['enabled']:
            tinc.service.enable()
        else:
            tinc.service.disable()
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
