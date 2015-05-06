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

from django import forms
from django.contrib import auth
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from plinth import actions
from plinth import cfg
from plinth.errors import ActionError, DomainRegistrationError
from plinth.modules.pagekite.utils import PREDEFINED_SERVICES, run
from plinth.modules.users.forms import GROUP_CHOICES
from plinth.utils import format_lazy
LOGGER = logging.getLogger(__name__)


class State1Form(auth.forms.UserCreationForm):
    """Firstboot state 1: create a new user."""
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(State1Form, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Create and log the user in."""
        user = super(State1Form, self).save(commit=commit)
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
    def render(self, *args, **kwargs):
        inputfield = super(SubdomainWidget, self).render(*args, **kwargs)
        domain = State5Form.DOMAIN_APPENDIX
        return """<div class="input-group">
                  {0}
                  <span class="input-group-addon">{1}</span>
               </div>""".format(inputfield, domain)


class State5Form(forms.Form):
    """Set up freedombox.me pagekite subdomain"""
    DOMAIN_APPENDIX = ".freedombox.me"
    # webservice url for domain validation and registration
    service_url = "http://freedombox.me/cgi-bin/freedomkite.pl"
    code_help_text = _("The voucher you received with your {box_name} Danube "
                       "Edition")
    code = forms.CharField(help_text=format_lazy(code_help_text,
                                                 box_name=_(cfg.box_name)))
    domain = forms.SlugField(label=_("Subdomain"),
                             widget=SubdomainWidget,
                             help_text=_("The subdomain you want to register"))

    def clean_domain(self):
        """Append the domain to the users' subdomain"""
        return self.cleaned_data['domain'] + self.DOMAIN_APPENDIX

    def clean(self):
        """Validate user input (subdomain and code)"""
        cleaned_data = super(State5Form, self).clean()
        # if the subdomain is wrong don't look if the domain is available
        if self.errors:
            return cleaned_data

        self.domain_already_registered = False
        code = cleaned_data.get("code")
        domain = cleaned_data.get("domain")

        response = requests.get(self.service_url, params={'code': code}).json()
        # The validation response looks like:
        # 1. code invalid: {}
        if 'domain' not in response:
            raise ValidationError(_('This code is not valid'), code='invalid')
        # 2. code valid, domain registered: {'domain': 'xx.freedombox.me'}
        elif response['domain']:
            if response['domain'] == domain:
                self.domain_already_registered = True
            else:
                msg = _('This code is bound to the domain %s' %
                        response['domain'])
                raise ValidationError(msg, code='invalid')
        # 3. code valid, no domain registered: {'domain': None}
        elif response['domain'] is None:
            # make sure that the desired domain is available
            data = {'domain': domain}
            domain_response = requests.get(self.service_url, params=data)
            registered_domain = domain_response.json()['domain']
            if registered_domain is not None:
                msg = _('The requested Domain is already registered')
                raise ValidationError(msg, code='invalid')

        return cleaned_data

    def register_domain(self):
        """Register a domain (only if it's not already registered)"""
        if not self.domain_already_registered:
            data = {'domain': self.cleaned_data['domain'],
                    'code': self.cleaned_data['code']}
            response = requests.post(self.service_url, data)
            if not response.ok:
                msg = "Domain registration failed: %s" % response.text
                LOGGER.error(msg)
                raise DomainRegistrationError(msg)

    def setup_pagekite(self):
        """Configure pagekite and enable the pagekite service"""
        # set kite name and secret
        run(['set-kite', '--kite-name', self.cleaned_data['domain']],
            input=self.cleaned_data['code'].encode())

        # set frontend
        run(['set-frontend', '%s:80' % self.cleaned_data['domain']])

        # enable pagekite http+https service
        for service_name in ['http', 'https']:
            service = PREDEFINED_SERVICES[service_name]['params']
            try:
                run(['add-service', '--service', json.dumps(service)])
            except ActionError as err:
                if 'already exists' not in str(err):
                    raise

        run(['start-and-enable'])
