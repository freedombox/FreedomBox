# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the dynamicsdns module.
"""

from django import forms
from django.core import validators
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from plinth import cfg
from plinth.utils import format_lazy


class ConfigureForm(forms.Form):
    """Form to configure the Dynamic DNS client."""
    help_update_url = \
        gettext_lazy('The Variables &lt;User&gt;, &lt;Pass&gt;, &lt;Ip&gt;, '
                     '&lt;Domain&gt; may be used within the URL. For details '
                     'see the update URL templates of the example providers.')
    help_service_type = \
        gettext_lazy('Please choose an update protocol according to your '
                     'provider. If your provider does not support the GnuDIP '
                     'protocol or your provider is not listed you may use '
                     'the update URL of your provider.')
    help_server = \
        gettext_lazy('Please do not enter a URL here (like '
                     '"https://example.com/") but only the hostname of the '
                     'GnuDIP server (like "example.com").')
    help_domain = format_lazy(
        gettext_lazy('The public domain name you want to use to reach your '
                     '{box_name}.'), box_name=gettext_lazy(cfg.box_name))
    help_disable_ssl_cert_check = \
        gettext_lazy('Use this option if your provider uses self signed '
                     'certificates.')
    help_use_http_basic_auth = \
        gettext_lazy('If this option is selected, your username and password '
                     'will be used for HTTP basic authentication.')
    help_password = \
        gettext_lazy('Leave this field empty if you want to keep your '
                     'current password.')
    help_username = \
        gettext_lazy('The username that was used when the account was '
                     'created.')

    provider_choices = (('gnudip', gettext_lazy('GnuDIP')),
                        ('noip.com', 'noip.com'), ('freedns.afraid.org',
                                                   'freedns.afraid.org'),
                        ('other', gettext_lazy('Other update URL')))

    service_type = forms.ChoiceField(label=gettext_lazy('Service Type'),
                                     help_text=help_service_type,
                                     choices=provider_choices)

    server = forms.CharField(
        label=gettext_lazy('GnuDIP Server Address'), required=False,
        help_text=help_server, validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      gettext_lazy('Invalid server name'))
        ])

    update_url = forms.CharField(label=gettext_lazy('Update URL'),
                                 required=False, help_text=help_update_url)

    disable_ssl_cert_check = forms.BooleanField(
        label=gettext_lazy('Accept all SSL certificates'),
        help_text=help_disable_ssl_cert_check, required=False)

    use_http_basic_auth = forms.BooleanField(
        label=gettext_lazy('Use HTTP basic authentication'),
        help_text=help_use_http_basic_auth, required=False)

    domain = forms.CharField(
        label=gettext_lazy('Domain Name'), help_text=help_domain,
        required=True, validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      gettext_lazy('Invalid domain name'))
        ])

    username = forms.CharField(label=gettext_lazy('Username'), required=False,
                               help_text=help_username)

    password = forms.CharField(label=gettext_lazy('Password'),
                               widget=forms.PasswordInput(), required=False,
                               help_text=help_password)

    show_password = forms.BooleanField(label=gettext_lazy('Show password'),
                                       required=False)

    use_ipv6 = forms.BooleanField(
        label=gettext_lazy('Use IPv6 instead of IPv4'), required=False)

    def clean(self):
        """Further validate and transform field data."""
        cleaned_data = super().clean()

        # Domain name is not case sensitive, but Let's Encrypt
        # certificate paths use lower-case domain name.
        cleaned_data['domain'] = cleaned_data['domain'].lower()

        update_url = cleaned_data.get('update_url')
        password = cleaned_data.get('password')
        service_type = cleaned_data.get('service_type')
        old_password = self.initial.get('password')

        if not password:
            # If password is not set, use old password
            cleaned_data['password'] = old_password

        message = _('This field is required.')
        if service_type == 'gnudip':
            for field_name in ['server', 'username', 'password']:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, message)
        else:
            if not update_url:
                self.add_error('update_url', message)

            param_map = (('username', '<User>'), ('password', '<Pass>'))
            for field_name, param in param_map:
                if (update_url and param in update_url
                        and not cleaned_data.get(field_name)):
                    self.add_error(field_name, message)

            if cleaned_data.get('use_http_basic_auth'):
                for field_name in ('username', 'password'):
                    if not cleaned_data.get(field_name):
                        self.add_error(field_name, message)

        del cleaned_data['show_password']
        return cleaned_data
