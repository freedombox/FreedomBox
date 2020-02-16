# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Module to provide API for showing notifications.
"""

import copy
import logging

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.exceptions import TemplateDoesNotExist
from django.template.response import SimpleTemplateResponse
from django.utils.translation import ugettext

from plinth import cfg

from . import models

severities = {'exception': 5, 'error': 4, 'warning': 3, 'info': 2, 'debug': 1}
logger = logging.getLogger(__name__)


class Notification(models.StoredNotification):
    """Wrapper over Notification model to provide the API."""
    class Meta:  # pylint: disable=too-few-public-methods
        """Meta properties of the Notification model."""
        proxy = True

    @property
    def severity_value(self):
        """Return severity as a numeric value suitable for comparison."""
        try:
            return severities[self.severity]
        except KeyError:
            return severities['info']

    def dismiss(self, should_dismiss=True):
        """Mark the notification as read or unread."""
        self.dismissed = should_dismiss
        super().save()

    def clean(self):
        """Perform additional validations on the model."""
        if self.severity not in ('exception', 'error', 'warning', 'info',
                                 'debug'):
            raise ValidationError('Invalid severity')

        if self.actions:
            self._validate_actions(self.actions)

        if (self.message or self.actions) and self.body_template:
            raise ValidationError(
                'Either body_template or message and actions must exist')

    @staticmethod
    def _validate_actions(actions):
        """Check that actions structure is valid."""
        if not isinstance(actions, list):
            raise ValidationError('Actions must be a list')

        for action in actions:
            if not isinstance(action, dict):
                raise ValidationError('Action must a dictionary')

            if 'type' not in action:
                raise ValidationError('Action must have a type')

            if action['type'] not in ('dismiss', 'link'):
                raise ValidationError('Action type must be dismiss or link')

            if action['type'] == 'dismiss':
                continue

            if 'text' not in action or 'url' not in action:
                raise ValidationError('Action must have text and url')

            if 'class' in action and action['class'] not in (
                    'primary', 'default', 'warning', 'danger', 'success',
                    'info'):
                raise ValidationError('Invalid action class')

    @staticmethod
    def update_or_create(**kwargs):
        """Update a notification or create one if necessary."""
        id = kwargs.pop('id')
        return Notification.objects.update_or_create(defaults=kwargs, id=id)[0]

    @staticmethod
    def get(key):  # pylint: disable=redefined-builtin
        """Return a notification with matching ID."""
        # pylint: disable=no-member
        try:
            return Notification.objects.get(pk=key)
        except Notification.DoesNotExist:
            raise KeyError('No such notification')

    @staticmethod
    def list(key=None, app_id=None, user=None, dismissed=False):
        """Return a list of notifications for a user."""
        filters = []
        if key:
            filters.append(Q(id=key))

        if app_id:
            filters.append(Q(app_id=app_id))

        if user:
            # XXX: Consider implementing caching for user groups
            groups = user.groups.values_list('name', flat=True)
            filters.append(Q(user__isnull=True) | Q(user=user.username))
            filters.append(Q(group__isnull=True) | Q(group__in=groups))

        if dismissed is not None:
            filters.append(Q(dismissed=dismissed))

        return Notification.objects.filter(*filters)[0:10]

    @staticmethod
    def _translate(string, data=None):
        """Translate a string for final display using data dict."""
        if not string:
            return None

        string = ugettext(string)
        try:
            string = str(string)
            if data:
                string = string.format(**data)
        except KeyError as error:
            logger.warning(
                'Notification missing required key during translation: %s',
                error)

        return string

    @staticmethod
    def _translate_dict(data_dict, data=None):
        """Translate strings inside a data dict for display."""
        if not data_dict:
            return data_dict

        new_dict = {}
        for key, value in data_dict.items():
            if isinstance(value, str) and value.startswith('translate:'):
                value = value.split(':', maxsplit=1)[1]
                value = Notification._translate(value, data)
            elif isinstance(value, dict):
                value = Notification._translate_dict(value, data)
            else:
                value = copy.deepcopy(value)

            new_dict[key] = value

        return new_dict

    @staticmethod
    def _render(template, data):
        """Use the template name and render it."""
        if not template:
            return None

        context = dict(data, box_name=ugettext(cfg.box_name))
        try:
            return SimpleTemplateResponse(template, context).render()
        except TemplateDoesNotExist:
            # Developer only error, no i18n
            return {'content': f'Template {template} does not exist.'.encode()}

    @staticmethod
    def get_display_context(user):
        """Return a list of notifications meant for display to a user."""
        notifications = Notification.list(user=user)
        max_severity = max(notifications, default=None,
                           key=lambda note: note.severity_value)
        max_severity = max_severity.severity if max_severity else None

        notes = []
        for note in notifications:
            data = Notification._translate_dict(note.data, note.data)
            actions = copy.deepcopy(note.actions)
            for action in actions:
                if 'text' in action:
                    action['text'] = Notification._translate(
                        action['text'], data)

            notes.append({
                'id': note.id,
                'app_id': note.app_id,
                'severity': note.severity,
                'title': Notification._translate(note.title, data),
                'message': Notification._translate(note.message, data),
                'body': Notification._render(note.body_template, data),
                'actions': actions,
                'data': data,
                'created_time': note.created_time,
                'last_update_time': note.last_update_time,
                'user': note.user,
                'group': note.group,
                'dismissed': note.dismissed,
            })

        return {'notifications': notes, 'max_severity': max_severity}
