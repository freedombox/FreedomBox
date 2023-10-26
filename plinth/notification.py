# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module to provide API for showing notifications."""

import copy
import logging
import string

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.exceptions import TemplateDoesNotExist
from django.template.response import SimpleTemplateResponse
from django.utils.translation import gettext

from plinth import cfg

from . import db, models

severities = {'exception': 5, 'error': 4, 'warning': 3, 'info': 2, 'debug': 1}
logger = logging.getLogger(__name__)


class Notification(models.StoredNotification):
    """API to create persistent global notifications to users.

    The number of notifications is shown on the top navigation bar of every
    page that the user loads. On clicking the notification icon, a full list of
    notifications is shown as a drop down that works on both on Desktop and
    Mobile interfaces.

    The notification API provides the following functionality.

    * Store the notifications on disk and persist them across restarts.

    * Update a notification for any of its stored details.

    * Show icon and name of the app that shows the notification.

    * Present the notification title and message.

    * Present actions that user can perform on the notification.

    * Allow for full customization of content and actions of the notification.
      This allows for use cases such as showing progress bar. This is done by
      allowing a custom template to be used for rendering.

    * Internationalization and localization of displayed notification.

    * Allow the notification to be dismissed and resurrected after dismissal.

    * Store arbitrary data as a dictionary along with the notification. This
      data is used for formatting localized strings and for rendering the
      custom template.

    * Limit a notification to a group of users or to a single user.

    * Retrieve a notification using specific string identifier.

    * Iterate all the notifications.

    * Filter notifications by app that created them, by whether the
      notification meant for a particular user and by whether a notification is
      dismissed or not.

    * Provide a convenient way to obtain the context for rendering templates
      that intend to show notifications.

    This class is a wrapper over Notification model to provide a simplified
    API. So, all of the Django model API is available on the class. The
    following fields are present in the model:

    'id' is a unique string identifier for the notification and acts as the
    primary key for the stored database table. Only the following chars are
    currently allowed: A-Z, a-z, 0-9, - and =. If other chars must be used, it
    is recommended to use base32 encoding.

    'app_id' is the unique ID of the app showing the notification.

    'severity' is a string indicating the severity of the notification which
    can take one of the following values: 'exception', 'error', 'warning',
    'info' and 'debug'.

    'title' is a user visible string that is the main heading of the
    notification. 'title' may be used to show a summary of notifications even
    'body_template' is used for customization. So, it is mandatory. The user
    who requested the operation that caused the notification may be different
    from the user that sees the notification. Each user wishes to see the
    notification in their own locale. This string is stored to the disk as it
    is. It is translated and then formatted with 'data' dictionary just before
    showing it to the user. So, it must be marked for translation with
    (u)gettext_noop but must not be translated using (u)gettext or similar
    methods.

    'message' is a user visible string that is the main body of the
    notification. It is formatted as a single paragraph. It is not used and
    must not be provided when 'body_template' is provided. It must be marked
    for translation but not translated similar to 'title'.

    'actions' is a list of dictionaries containing information about what
    operations, such as dismiss, that the user may perform on the notification.
    When not provided, no actions are shown and the notification can't be
    dismissed. It is not used and must not be provided when 'body_template' is
    provided. When 'body_template' is provided, the template is expected to
    list its actions inside the template.

    A example of 'actions' structure is as follows: [{'type': 'dismiss'},
    {'type': 'link', 'class': 'warning', 'text': 'Cleanup', 'url':
    'storage:index'}]. The 'type' parameter can be 'dismiss' or 'link'. When
    'dismiss' is the type, no other information is necessary and a simple
    action to dismiss the notification is provided. When the 'type' is 'link',
    a button is shown with label provided by 'text'. The 'text' property is
    must be marked for translation but not translated similar to 'title'. When
    the button is clicked, it will direct the user to the Django URL indicated
    by 'url'. 'class' is used for CSS styling of the button. It can taken on
    any of the following values; 'primary', 'default', 'warning', 'danger',
    'success', 'info'.

    'body_template' is the name of the Django template to use instead of
    'title', 'message' and 'actions'. It enables the the notification creator
    to go beyond the simple presentation offered by default and include rich
    content such as progress bars and forms inside a notification. The template
    itself is expected to contain a meaningful title, body and operations to be
    performed on the notification. It is an error to provide 'body_template'
    and any one of 'message' and 'actions' at the same time. 'title' may still
    be used when notifications are presented in other situations. The template
    is rendered with 'data' as it's context. So, any key/values to be included
    in the context must become part of the 'data'.

    'data' is a custom dictionary that is serialized and stored along with the
    notification. It is has three purposes; to format the translated strings
    before showing to the user, to be used as context for rendering a custom
    template and to store any extra data associated with the notification on
    behalf of the it's creator for future reference. Any string value in the
    dictionary, even in deeper levels, if prefixed by 'translate:' will be
    translated before being used.

    'created_time' is a date/time field that is automatically populated when
    the notification is created.

    'last_update_time' is a date/time field that is automatically modified when
    the notification is updated with newer properties, including changes to the
    'dismissed' property.

    'user' is the username of the account to which this notification should be
    shown to. When not provided or set to None, it means that the notification
    is meant for all the users (subject to 'group' restriction).

    'group' is the group of users to which this notification should be shown
    to. When not provided or set to None, it means that the notification is
    meant for all the users (subject to 'user' restriction). If a user in the
    group dismisses the notification, it is no longer shown to other users. To
    let each user see the notification, create multiple notifications each
    restricted to a single user account instead.

    'dismissed' is a boolean flag that indicates whether the notification has
    been dismissed by the user.

    """

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
        """Mark the notification as read or unread.

        If 'should_dismiss' is True, the notification is dismissed else the
        notification is resurrected even after being dismissed.

        """
        self.dismissed = should_dismiss
        with db.lock:
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
        """Update a notification or create one if necessary.

        'id' field will be used to retrieve the notification and all other
        fields values will be updated after retrieval. If not match is found, a
        new notification is created and returned.

        """
        id = kwargs.pop('id')
        with db.lock:
            return Notification.objects.update_or_create(
                defaults=kwargs, id=id)[0]

    @staticmethod
    def get(key):  # pylint: disable=redefined-builtin
        """Return a notification object with a matching ID."""
        # pylint: disable=no-member
        with db.lock:
            try:
                return Notification.objects.get(pk=key)
            except Notification.DoesNotExist:
                raise KeyError('No such notification')

    @staticmethod
    def list(key=None, app_id=None, user=None, dismissed=False):
        """Return a list of notifications for a user.

        'key' if provided, return only notifications that match this value as
        their 'id'.

        'app_id' if provided, return only notifications that match this
        app_id.

        'user' must be a Django request.user structure. If provided, only
        notifications that are meant for this user account specifically or
        meant for any of groups that this user belongs to will be returned.

        'dismissed' is the a boolean flag or None. If not None, only
        notifications with the matching in their 'dismissed' field will be
        returned.

        """
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

        with db.lock:
            return Notification.objects.filter(*filters)[0:10]

    @staticmethod
    def _translate(string_, data=None):
        """Translate a string for final display using data dict."""
        if not string_:
            return None

        string_ = gettext(string_)
        try:
            string_ = str(string_)
            if data:
                string_ = SafeFormatter().vformat(string_, [], data)
        except KeyError as error:
            logger.warning(
                'Notification missing required key during translation: %s',
                error)

        return string_

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
    def _render(request, template, context):
        """Use the template name and render it."""
        if not template:
            return None

        context = dict(context, box_name=gettext(cfg.box_name),
                       request=request)
        try:
            return SimpleTemplateResponse(template, context).render()
        except TemplateDoesNotExist:
            # Developer only error, no i18n
            return {'content': f'Template {template} does not exist.'.encode()}

    @staticmethod
    def get_display_context(request, user):
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

            note_context = {
                'id': note.id,
                'app_id': note.app_id,
                'severity': note.severity,
                'title': Notification._translate(note.title, data),
                'message': Notification._translate(note.message, data),
                'actions': actions,
                'data': data,
                'created_time': note.created_time,
                'last_update_time': note.last_update_time,
                'user': note.user,
                'group': note.group,
                'dismissed': note.dismissed,
            }
            body = Notification._render(request, note.body_template,
                                        note_context)
            note_context['body'] = body
            notes.append(note_context)

        return {'notifications': notes, 'max_severity': max_severity}


class SafeFormatter(string.Formatter):
    """A string.format() handler to deal with missing arguments."""

    def get_value(self, key, args, kwargs):
        """Retrieve a given field value."""
        try:
            return super().get_value(key, args, kwargs)
        except (IndexError, KeyError):
            return f'?{key}?'
