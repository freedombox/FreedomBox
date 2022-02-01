# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the dynamicsdns module.
"""

import logging

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from plinth import actions
from plinth.modules import dynamicdns
from plinth.signals import domain_added, domain_removed

from .forms import ConfigureForm

logger = logging.getLogger(__name__)

EMPTYSTRING = 'none'


def index(request):
    """Serve the configuration form."""
    status = dynamicdns.get_status()
    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, initial=status)
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = dynamicdns.get_status()
            form = ConfigureForm(initial=status)
    else:
        form = ConfigureForm(initial=status)

    return TemplateResponse(
        request, 'dynamicdns.html', {
            'title': _('Configure Dynamic DNS'),
            'app_info': dynamicdns.app.info,
            'form': form,
            'status': get_status()
        })


def get_status():
    """Return the current status."""
    check_nat = _run(['get-nat'])
    last_update = _run(['get-last-success'])

    no_nat = check_nat.strip() == 'no'
    nat_unchecked = check_nat.strip() == 'unknown'
    timer = _run(['get-timer'])

    return {
        'no_nat': no_nat,
        'nat_unchecked': nat_unchecked,
        'timer': timer,
        'last_update': last_update,
    }


def _apply_changes(request, old_status, new_status):
    """Apply the changes to Dynamic DNS client."""
    logger.info('New status is - %s', new_status)
    logger.info('Old status was - %s', old_status)

    if new_status['dynamicdns_secret'] == '':
        new_status['dynamicdns_secret'] = old_status['dynamicdns_secret']

    if new_status['dynamicdns_ipurl'] == '':
        new_status['dynamicdns_ipurl'] = EMPTYSTRING

    if new_status['dynamicdns_update_url'] == '':
        new_status['dynamicdns_update_url'] = EMPTYSTRING

    if new_status['dynamicdns_server'] == '':
        new_status['dynamicdns_server'] = EMPTYSTRING

    if new_status['service_type'] == 'GnuDIP':
        new_status['dynamicdns_update_url'] = EMPTYSTRING
    else:
        new_status['dynamicdns_server'] = EMPTYSTRING

    if old_status != new_status:
        disable_ssl_check = "disabled"
        use_http_basic_auth = "disabled"
        use_ipv6 = "disabled"

        if new_status['disable_SSL_cert_check']:
            disable_ssl_check = "enabled"

        if new_status['use_http_basic_auth']:
            use_http_basic_auth = "enabled"

        if new_status.get('use_ipv6'):
            use_ipv6 = "enabled"

        # Domain name is not case sensitive, but Let's Encrypt
        # certificate paths use lower-case domain name.
        new_domain_name = new_status['dynamicdns_domain'].lower()

        _run([
            'configure',
            '-s',
            new_status['dynamicdns_server'],
            '-d',
            new_domain_name,
            '-u',
            new_status['dynamicdns_user'],
            '-p',
            '-I',
            new_status['dynamicdns_ipurl'],
            '-U',
            new_status['dynamicdns_update_url'],
            '-c',
            disable_ssl_check,
            '-b',
            use_http_basic_auth,
            '-6',
            use_ipv6,
        ], input=new_status['dynamicdns_secret'].encode())

        if old_status['enabled']:
            domain_removed.send_robust(sender='dynamicdns',
                                       domain_type='domain-type-dynamic',
                                       name=old_status['dynamicdns_domain'])
            _run(['stop'])

        if new_status['enabled']:
            domain_added.send_robust(sender='dynamicdns',
                                     domain_type='domain-type-dynamic',
                                     name=new_domain_name, services='__all__')
            _run(['start'])

        messages.success(request, _('Configuration updated'))
    else:
        logger.info('Nothing changed')


def _run(arguments, input=None):
    """Run a given command and raise exception if there was an error."""
    return actions.superuser_run('dynamicdns', arguments, input=input)
