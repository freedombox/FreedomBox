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
Forms for first boot module.
"""

import json
import logging
import requests
import subprocess

from django import forms
from django.contrib import auth
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _, ugettext_lazy

from plinth import actions
from plinth import cfg
from plinth.errors import ActionError, DomainRegistrationError
from plinth.modules.pagekite.utils import PREDEFINED_SERVICES, run
from plinth.modules.security import set_restricted_access
from plinth.modules.users.forms import GROUP_CHOICES, ValidNewUsernameCheckMixin
from plinth.utils import format_lazy

logger = logging.getLogger(__name__)


class State1Form(ValidNewUsernameCheckMixin, auth.forms.UserCreationForm):
    """Firstboot state 1: create a new user."""
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        """Create and log the user in."""
        user = super().save(commit=commit)
        if commit:
            try:
                actions.superuser_run(
                    'ldap',
                    ['create-user', user.get_username()],
                    input=self.cleaned_data['password1'].encode())
            except ActionError:
                messages.error(self.request,
                               _('Creating LDAP user failed.'))

            try:
                actions.superuser_run(
                    'ldap',
                    ['add-user-to-group', user.get_username(), 'admin'])
            except ActionError:
                messages.error(self.request,
                               _('Failed to add new user to admin group.'))

            # Create initial Django groups
            for group_choice in GROUP_CHOICES:
                auth.models.Group.objects.get_or_create(name=group_choice[0])

            admin_group = auth.models.Group.objects.get(name='admin')
            admin_group.user_set.add(user)

            self.login_user(self.cleaned_data['username'],
                            self.cleaned_data['password1'])

            # Restrict console login to users in admin or sudo group
            try:
                set_restricted_access(True)
                message = _('Console login access restricted to users in '
                            '"admin" group. This can be configured in '
                            'security settings.')
                messages.success(self.request, message)
            except Exception:
                messages.error(self.request,
                               _('Failed to restrict console access.'))

        return user

    def login_user(self, username, password):
        """Try to login the user with the credentials provided"""
        try:
            user = auth.authenticate(username=username, password=password)
            auth.login(self.request, user)
        except Exception:
            pass
        else:
            message = _('User account created, you are now logged in')
            messages.success(self.request, message)


class SubdomainWidget(forms.widgets.TextInput):
    """Append the domain to the subdomain bootstrap input field"""
    def __init__(self, domain, *args, **kwargs):
        """Intialize the widget by storing the domain value."""
        super().__init__(*args, **kwargs)
        self.domain = domain

    def render(self, *args, **kwargs):
        """Return the HTML for the widget."""
        inputfield = super().render(*args, **kwargs)
        return """<div class="input-group">
                  {0}
                  <span class="input-group-addon">{1}</span>
               </div>""".format(inputfield, self.domain)


class State5Form(forms.Form):
    """Set up freedombox.me pagekite subdomain"""
    DOMAIN_APPENDIX = '.freedombox.me'
    # Webservice url for domain validation and registration
    service_url = 'http://freedombox.me/cgi-bin/freedomkite.pl'

    code_help_text = format_lazy(
        ugettext_lazy('The voucher you received with your {box_name} Danube '
                      'Edition'), box_name=ugettext_lazy(cfg.box_name))

    code = forms.CharField(help_text=code_help_text)

    domain = forms.SlugField(label=_('Subdomain'),
                             widget=SubdomainWidget(domain=DOMAIN_APPENDIX),
                             help_text=_('The subdomain you want to register'))

    def clean_domain(self):
        """Append the domain to the users' subdomain"""
        return self.cleaned_data['domain'] + self.DOMAIN_APPENDIX

    def clean(self):
        """Validate user input (subdomain and code)"""
        cleaned_data = super().clean()

        # If the subdomain is wrong, don't look if the domain is
        # available
        if self.errors:
            return cleaned_data

        self.domain_already_registered = False
        code = cleaned_data.get('code')
        domain = cleaned_data.get('domain')

        response = requests.get(self.service_url, params={'code': code}).json()

        # 1. Code is invalid: {}
        if 'domain' not in response:
            raise ValidationError(_('This code is not valid'), code='invalid')
        # 2. Code is valid, domain registered: {'domain': 'xx.freedombox.me'}
        elif response['domain']:
            if response['domain'] == domain:
                self.domain_already_registered = True
            else:
                message = _('This code is bound to the domain {domain}.') \
                    .format(domain=response['domain'])
                raise ValidationError(message, code='invalid')
        # 3. Code is valid, no domain registered: {'domain': None}
        elif response['domain'] is None:
            # Make sure that the desired domain is available
            data = {'domain': domain}
            domain_response = requests.get(self.service_url, params=data)
            registered_domain = domain_response.json()['domain']
            if registered_domain is not None:
                message = _('The requested domain is already registered.')
                raise ValidationError(message, code='invalid')

        return cleaned_data

    def register_domain(self):
        """Register a domain (only if it's not already registered)"""
        if self.domain_already_registered:
            return

        data = {'domain': self.cleaned_data['domain'],
                'code': self.cleaned_data['code']}
        response = requests.post(self.service_url, data)
        if not response.ok:
            message = _('Domain registration failed: {response}.').format(
                response=response.text)
            logger.error(message)
            raise DomainRegistrationError(message)

    def setup_pagekite(self):
        """Configure and enable PageKite service."""
        # Set kite name and secret
        run(['set-kite', '--kite-name', self.cleaned_data['domain']],
            input=self.cleaned_data['code'].encode())

        # Set frontend
        run(['set-frontend', '%s:80' % self.cleaned_data['domain']])

        # Enable PageKite HTTP + HTTPS service
        for service_name in ['http', 'https']:
            service = PREDEFINED_SERVICES[service_name]['params']
            try:
                run(['add-service', '--service', json.dumps(service)])
            except ActionError as err:
                if 'already exists' not in str(err):
                    raise

        run(['start-and-enable'])
