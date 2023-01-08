# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django form for configuring Gitweb.
"""

import re
from urllib.parse import urlparse

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

from plinth.modules import gitweb

from . import privileged
from .manifest import REPO_DIR_OWNER


def _get_branches(repo):
    """Get all the branches in the repository."""
    branch_data = privileged.get_branches(repo, _run_as_user=REPO_DIR_OWNER)
    default_branch = branch_data['default_branch']
    branches = branch_data['branches']

    if default_branch not in branches:
        branches.insert(0, default_branch)

    return [(branch, branch) for branch in branches]


def get_name_from_url(url):
    """Get a repository name from URL"""
    return urlparse(url).path.split('/')[-1]


def is_repo_url(url):
    """Check if URL is valid."""
    try:
        RepositoryValidator(input_should_be='url')(url)
    except ValidationError:
        return False

    return True


class RepositoryValidator:
    input_should_be = 'name'

    def __init__(self, input_should_be=None):
        if input_should_be is not None:
            self.input_should_be = input_should_be

    def __call__(self, value):
        """Validate that the input is a correct repository name or URL"""
        if self.input_should_be in ('url', 'url_or_name'):
            try:
                URLValidator(schemes=['http', 'https'],
                             message=_('Invalid repository URL.'))(value)
            except ValidationError:
                if self.input_should_be == 'url':
                    raise
            else:
                value = get_name_from_url(value)

        if (not re.match(r'^[a-zA-Z0-9-._]+$', value)) \
                or value.startswith(('-', '.')) \
                or value.endswith('.git.git'):
            raise ValidationError(_('Invalid repository name.'), 'invalid')


class CreateRepoForm(forms.Form):
    """Form to create and edit a new repository."""

    name = forms.CharField(
        label=_(
            'Name of a new repository or URL to import an existing repository.'
        ), strip=True,
        validators=[RepositoryValidator(input_should_be='url_or_name')],
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    description = forms.CharField(
        label=_('Description of the repository'), strip=True, required=False,
        help_text=_('Optional, for displaying on Gitweb.'))

    owner = forms.CharField(label=_('Repository\'s owner name'), strip=True,
                            required=False,
                            help_text=_('Optional, for displaying on Gitweb.'))

    is_private = forms.BooleanField(
        label=_('Private repository'), required=False,
        help_text=_('Allow only authorized users to access this repository.'))

    def __init__(self, *args, **kwargs):
        """Initialize the form with extra request argument."""
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'autofocus': 'autofocus'})

    def clean_name(self):
        """Check if the name is valid."""
        name = self.cleaned_data['name']

        repo_name = name
        if is_repo_url(name):
            repo_name = get_name_from_url(name)

        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]

        for repo in gitweb.get_repo_list():
            if repo_name == repo['name']:
                raise ValidationError(
                    _('A repository with this name already exists.'))

        if is_repo_url(name):
            if not privileged.repo_exists(name):
                raise ValidationError('Remote repository is not available.')

        return name


class EditRepoForm(CreateRepoForm):
    """Form to create and edit a new repository."""

    name = forms.CharField(
        label=_('Name of the repository'),
        strip=True,
        validators=[RepositoryValidator()],
        help_text=_(
            'An alpha-numeric string that uniquely identifies a repository.'),
    )

    default_branch = forms.ChoiceField(
        label=_('Default branch'),
        help_text=_('Gitweb displays this as a default branch.'))

    def __init__(self, *args, **kwargs):
        """Initialize the form with extra request argument."""
        super().__init__(*args, **kwargs)
        branches = _get_branches(self.initial['name'])
        self.fields['default_branch'].choices = branches

    def clean_name(self):
        """Check if the name is valid."""
        name = self.cleaned_data['name']
        if 'name' in self.initial and name == self.initial['name']:
            return name

        if name.endswith('.git'):
            name = name[:-4]

        for repo in gitweb.get_repo_list():
            if name == repo['name']:
                raise ValidationError(
                    _('A repository with this name already exists.'))

        return name
