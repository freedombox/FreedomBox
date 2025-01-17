# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for the names app."""

import re

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy

HOSTNAME_REGEX = r'^[a-zA-Z0-9]([-a-zA-Z0-9]{,61}[a-zA-Z0-9])?$'


class NamesConfigurationForm(forms.Form):
    """Form to configure names app."""

    dns_over_tls = forms.ChoiceField(
        label=_('Use DNS-over-TLS for resolving domains (global preference)'),
        widget=forms.RadioSelect, choices=[
            ('yes',
             format_lazy(
                 'Yes. Encrypt connections to the DNS server. <p '
                 'class="help-block">This improves privacy as domain name '
                 'queries will not be made as plain text over the network. It '
                 'also improves security as responses from the server cannot '
                 'be manipulated. If the configured DNS servers do not '
                 'support DNS-over-TLS, all name resolutions will fail. If '
                 'your DNS provider (likely your ISP) does not support '
                 'DNS-over-TLS or blocks some domains, you can configure '
                 'well-known public DNS servers in individual network '
                 'connection settings.</p>', allow_markup=True)),
            ('opportunistic',
             format_lazy(
                 'Opportunistic. <p class="help-block">Encrypt connections to '
                 'the DNS server if the server supports DNS-over-TLS. '
                 'Otherwise, use unencrypted connections. There is no '
                 'protection against response manipulation.</p>',
                 allow_markup=True)),
            ('no',
             format_lazy(
                 'No. <p class="help-block">Do not encrypt domain name '
                 'resolutions.</p>', allow_markup=True)),
        ], initial='no')

    dnssec = forms.ChoiceField(
        label=_('Use DNSSEC when resolving domains (global preference)'),
        widget=forms.RadioSelect, choices=[
            ('yes',
             format_lazy(
                 'Yes. Verify authenticity and integrity of domain '
                 'resolutions. <p class="help-block">This improves security. '
                 'If the configured DNS servers do not support DNSSEC, all '
                 'name resolutions will fail. If your DNS provider (likely '
                 'your ISP) does not support DNSSEC or is manipulating '
                 'responses, you can configure well-known public DNS servers '
                 'in individual network connection settings.</p>',
                 allow_markup=True)),
            ('allow-downgrade',
             format_lazy(
                 'Allow downgrade. <p class="help-block">Verify name '
                 'resolutions done by the DNS server if the server supports '
                 'DNSSEC. Otherwise, allow unverified resolutions. Limited '
                 'improvement to security. Detecting whether a DNS server '
                 'supports DNSSEC is not very reliable currently.</p>',
                 allow_markup=True)),
            ('no',
             format_lazy(
                 'No. <p class="help-block">Do not verify domain name '
                 'resolutions.</p>', allow_markup=True)),
        ], initial='no')


class HostnameForm(forms.Form):
    """Form to update system's hostname."""
    # See:
    # https://tools.ietf.org/html/rfc952
    # https://tools.ietf.org/html/rfc1035#section-2.3.1
    # https://tools.ietf.org/html/rfc1123#section-2
    # https://tools.ietf.org/html/rfc2181#section-11
    hostname = forms.CharField(
        label=_('Hostname'), help_text=format_lazy(
            _('Hostname is the local name by which other devices on the local '
              'network can reach your {box_name}.  It must start and end with '
              'an alphabet or a digit and have as interior characters only '
              'alphabets, digits and hyphens.  Total length must be 63 '
              'characters or less.'), box_name=_(cfg.box_name)), validators=[
                  validators.RegexValidator(HOSTNAME_REGEX,
                                            _('Invalid hostname'))
              ], strip=True)


def _domain_label_validator(domain_name):
    """Validate domain name labels."""
    for label in domain_name.split('.'):
        if not re.match(HOSTNAME_REGEX, label):
            raise ValidationError(_('Invalid domain name'))


class DomainAddForm(forms.Form):
    """Form to add a static domain name."""

    domain_name = forms.CharField(
        label=_('Domain Name'), help_text=format_lazy(
            _('Domain name is the global name by which other devices on the '
              'Internet can reach your {box_name}.  It must consist of '
              'labels separated by dots.  Each label must start and end '
              'with an alphabet or a digit and have as interior characters '
              'only alphabets, digits and hyphens.  Length of each label '
              'must be 63 characters or less.  Total length of domain name '
              'must be 253 characters or less.'), box_name=_(cfg.box_name)),
        required=True, validators=[
            validators.RegexValidator(
                r'^[a-zA-Z0-9]([-a-zA-Z0-9.]{,251}[a-zA-Z0-9])?$',
                _('Invalid domain name')), _domain_label_validator
        ], strip=True)
