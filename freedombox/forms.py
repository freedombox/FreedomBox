# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Common forms for use by modules.
"""

import os

from django import forms
from django.conf import settings
from django.utils import translation
from django.utils.translation import get_language_info
from django.utils.translation import gettext_lazy as _

import plinth


def _get_repository_choices():
    """Return the list of available repositories."""
    import plinth.modules.backups.repository as repository_module
    choices = [(repository.uuid, repository.name)
               for repository in repository_module.get_repositories()
               if repository.is_usable()]

    return choices


class AppEnableDisableForm(forms.Form):
    """Form to enable / disable an app."""
    should_enable = forms.BooleanField(widget=forms.HiddenInput,
                                       required=False)


class UninstallForm(forms.Form):
    """Form to uninstall an app."""
    should_backup = forms.BooleanField(
        label=_('Backup app before uninstall'),
        help_text=_('Restoring from the backup will restore app data.'),
        required=False, initial=True)
    repository = forms.ChoiceField(label=_('Repository to backup to'),
                                   choices=_get_repository_choices)

    def __init__(self, **kwargs):
        """Determine if backup fields must be used."""
        has_backup_restore = kwargs.pop('has_backup_restore', True)
        super().__init__(**kwargs)
        if not has_backup_restore:
            del self.fields['should_backup']
            del self.fields['repository']


class DomainSelectionForm(forms.Form):
    """Form for selecting a domain name."""

    def __init__(self, show_none=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from plinth.modules.names.components import DomainName
        domains = list(DomainName.list_names())

        choices = list(zip(domains, domains))
        if show_none:
            choices = [('', _('(None)'))] + choices
            self.fields['domain_name'].required = False

        self.fields['domain_name'].choices = choices

    domain_name = forms.ChoiceField(
        label=_('Select a domain name to be used with this application'))


def _get_domain_choices():
    """Double domain entries for inclusion in the choice field."""
    from plinth.modules.names import get_available_tls_domains
    return ((domain, domain) for domain in get_available_tls_domains())


class TLSDomainForm(forms.Form):
    """Form to select a TLS domain for an app."""
    domain = forms.ChoiceField(
        choices=_get_domain_choices,
        label=_('TLS domain'),
        help_text=_(
            'Select a domain to use TLS with. If the list is empty, please '
            'configure at least one domain with certificates.'),
        required=False,
    )


class LanguageSelectionFormMixin:
    """Form mixin for selecting the user's preferred language."""

    language = forms.ChoiceField(
        label=_('Language'),
        help_text=_('Language to use for presenting this web interface'),
        required=False)

    def __init__(self, *args, **kwargs):
        """Initialize the form to fill language choice values."""
        super().__init__(*args, **kwargs)
        supported_languages = [
            (None, _('Use the language preference set in the browser'))
        ]

        def _get_local_name(language_code, language_name):
            try:
                return get_language_info(language_code)['name_local']
            except KeyError:
                return language_name

        for language_code, language_name in settings.LANGUAGES:
            locale_code = translation.to_locale(language_code)
            plinth_dir = os.path.dirname(plinth.__file__)
            if language_code == 'en' or os.path.exists(
                    os.path.join(plinth_dir, 'locale', locale_code)):
                supported_languages.append(
                    (language_code,
                     _get_local_name(language_code, language_name)))

        self.fields['language'].choices = supported_languages


class LanguageSelectionForm(LanguageSelectionFormMixin, forms.Form):
    """Language selection form."""

    language = LanguageSelectionFormMixin.language


class CheckboxSelectMultipleWithReadOnly(forms.widgets.CheckboxSelectMultiple):
    """Multiple checkbox widget that allows setting individual fields readonly.

    To mark a feature as readonly an option, pass a dict instead of a string
    for its label, of the form: {'label': 'option label', 'disabled': True}.

    """

    def create_option(self, name, value, label, selected, index, subindex=None,
                      attrs=None):
        option = super().create_option(name, value, label, selected, index,
                                       subindex, attrs)
        if isinstance(option['label'], dict):
            if option['label'].get('disabled'):
                option['attrs']['disabled'] = 'disabled'

            option['label'] = option['label']['label']

        return option


class CheckboxSelectMultiple(forms.widgets.CheckboxSelectMultiple):
    """CheckboxSelectMultiple with ids named after choices."""

    def id_for_label(self, id_, index=None):
        """
        Make ids looks like id_groups_groupname where
        a choice is like ('groupname', 'Group description').
        """
        if index is None:
            return ''
        if id_ and self.add_id_index:
            id_ = '%s_%s' % (id_, list(self.choices)[int(index)][0])
        return id_
