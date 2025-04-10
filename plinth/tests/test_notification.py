# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Notification, API to show notificatoins.
"""

import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from plinth.notification import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture(name='note')
def fixture_note():
    """Fixture to return a valid notification object."""
    Notification.objects.all().delete()
    return Notification.update_or_create(id='test-notification',
                                         app_id='test-app', severity='info',
                                         title='Test Title',
                                         data={'test-key': 'test-value'})


@pytest.fixture(name='user')
def fixture_user():
    """Fixture to create a new user for tests."""
    group = Group(name='test-group')
    group.save()

    user = User(username='test-user')
    user.save()
    user.groups.add(group)
    user.save()

    return user


@pytest.mark.parametrize('severity,severity_value', [('exception', 5),
                                                     ('error', 4),
                                                     ('warning', 3),
                                                     ('info', 2), ('debug', 1),
                                                     ('x-invalid', 2)])
def test_severity_value(note, severity, severity_value):
    """Test that severity_value is mapper properly."""
    note.severity = severity
    assert note.severity_value == severity_value


def test_dismiss(note):
    """Test that setting dismissed value works."""
    note.dismiss()
    assert note.dismissed
    Notification.get('test-notification') == note  # Saved

    note.dismiss(should_dismiss=True)
    assert note.dismissed

    note.dismiss(should_dismiss=False)
    assert not note.dismissed


def test_severity_invalid_value(note):
    """Test valid values for severity."""
    note.severity = 'x-invalid-value'
    with pytest.raises(ValidationError):
        note.clean()


@pytest.mark.parametrize('severity',
                         ['exception', 'error', 'warning', 'info', 'debug'])
def test_severity_valid_values(note, severity):
    """Test that valid values are accepted for severity."""
    note.severity = severity
    note.clean()


@pytest.mark.parametrize('values', [
    [None, None, None],
    ['Message', None, None],
    [None, [{
        'type': 'dismiss'
    }], None],
    [None, None, 'test-template.html'],
])
def test_valid_message_actions_body_template(note, values):
    """Test valid values for message/actions/body_template."""
    note.message = values[0]
    note.actions = values[1]
    note.body_template = values[2]
    note.clean()


@pytest.mark.parametrize('values', [
    ['Message', None, 'test-template.html'],
    [None, [{
        'type': 'dismiss'
    }], 'test-template.html'],
])
def test_invalid_message_actions_body_template(note, values):
    """Test invalid values for message/actions/body_template."""
    note.message = values[0]
    note.actions = values[1]
    note.body_template = values[2]
    with pytest.raises(ValidationError):
        note.clean()


@pytest.mark.parametrize('actions', [
    None,
    [],
    [{
        'type': 'dismiss'
    }],
    [{
        'type': 'dismiss'
    }, {
        'type': 'dismiss'
    }],
    [{
        'type': 'dismiss',
        'extra-key': 'extra-value'
    }],
    [{
        'type': 'link',
        'text': 'Test',
        'url': 'test-url'
    }],
    [{
        'type': 'link',
        'text': 'Test',
        'url': 'test-url',
        'class': 'primary'
    }],
    [{
        'type': 'link',
        'text': 'Test',
        'url': 'test-url',
        'class': 'default'
    }],
    [{
        'type': 'link',
        'text': 'Test',
        'url': 'test-url',
        'class': 'warning'
    }],
    [{
        'type': 'link',
        'text': 'Test',
        'url': 'test-url',
        'class': 'danger'
    }],
    [{
        'type': 'link',
        'text': 'Test',
        'url': 'test-url',
        'class': 'success'
    }],
    [{
        'type': 'link',
        'text': 'Test',
        'url': 'test-url',
        'class': 'info'
    }],
])
def test_valid_actions(note, actions):
    """Test valid values for actions."""
    note.actions = actions
    note.clean()


@pytest.mark.parametrize('actions', [
    'actions',
    [[]],
    [None],
    ['action'],
    [{}],
    [{
        'test-key': 'test-value'
    }],
    [{
        'type': 'invalid-type'
    }],
    [{
        'type': 'link'
    }],
    [{
        'type': 'link',
        'text': 'Test'
    }],
    [{
        'type': 'link',
        'url': 'test-url'
    }],
    [{
        'type': 'link',
        'url': 'test-url',
        'text': 'Test',
        'class': 'invalid-class'
    }],
])
def test_invalid_actions(note, actions):
    """Test invalid values for actions."""
    note.actions = actions
    with pytest.raises(ValidationError):
        note.clean()


def test_update(note):
    """Test updating a existing notification."""
    note = Notification.get('test-notification')
    assert note.app_id == 'test-app'
    assert note.severity == 'info'
    assert note.title == 'Test Title'
    assert note.data == {'test-key': 'test-value'}

    Notification.update_or_create(id='test-notification', app_id='test-app2',
                                  severity='error', title='Test Title2',
                                  data={'test-key2': 'test-value2'})
    note = Notification.get('test-notification')
    assert note.app_id == 'test-app2'
    assert note.severity == 'error'
    assert note.title == 'Test Title2'
    assert note.data == {'test-key2': 'test-value2'}


def test_create(note):
    """Test creating a new notification works."""
    note.delete()
    note.update_or_create(id='test-notification', app_id='test-app2',
                          severity='error', title='Test Title2',
                          data={'test-key2': 'test-value2'})
    note = Notification.get('test-notification')
    assert note.app_id == 'test-app2'
    assert note.severity == 'error'
    assert note.title == 'Test Title2'
    assert note.data == {'test-key2': 'test-value2'}


def test_delete(note):
    """Test deleting a new notification works."""
    note.delete()
    with pytest.raises(KeyError):
        Notification.get('test-notification')


def test_get(note):
    """Test retrieving a notification."""
    assert Notification.get('test-notification') == note

    note.delete()
    with pytest.raises(KeyError):
        Notification.get('test-notification')


def test_list_filter_key(note):
    """Test that list filter with key works."""
    assert list(Notification.list(key='invalid')) == []
    assert list(Notification.list(key='test-notification')) == [note]
    assert list(Notification.list()) == [note]


def test_list_filter_app_id(note):
    """Test that list filter with app_id works."""
    assert list(Notification.list(app_id='invalid')) == []
    assert list(Notification.list(app_id='test-app')) == [note]
    assert list(Notification.list()) == [note]


def test_list_filter_dismissed(note):
    """Test that list filter with dismissed works."""
    assert list(Notification.list(dismissed=True)) == []
    assert list(Notification.list(dismissed=False)) == [note]
    assert list(Notification.list(dismissed=None)) == [note]
    note.dismiss()
    assert list(Notification.list(dismissed=True)) == [note]
    assert list(Notification.list(dismissed=False)) == []
    assert list(Notification.list(dismissed=None)) == [note]


def test_list_filter_user(note, user):
    """Test that list filter with user works."""
    # Invalid user set on notification
    note.user = 'invalid-user'
    note.save()
    assert list(Notification.list(user=user)) == []

    # Valid user set on notification
    note.user = 'test-user'
    note.save()
    assert list(Notification.list(user=user)) == [note]


def test_list_filter_group(note, user):
    """Test that list filter with group works."""
    # Invalid group set on notification
    note.group = 'invalid-group'
    note.save()
    assert list(Notification.list(user=user)) == []

    # Valid group set on notification
    note.group = 'test-group'
    note.save()
    assert list(Notification.list(user=user)) == [note]


def test_list_filter_user_and_group(note, user):
    """Test that list filter with group works."""
    # No user/group filter
    assert list(Notification.list()) == [note]

    # No user/group set on notification
    assert list(Notification.list(user=user)) == [note]

    # Invalid user set on notification
    note.user = 'invalid-user'
    note.group = 'test-group'
    note.save()
    assert list(Notification.list(user=user)) == []

    # Invalid group set on notification
    note.user = 'test-user'
    note.group = 'invalid-group'
    note.save()
    assert list(Notification.list(user=user)) == []

    # Valid user and group set on notification
    note.user = 'test-user'
    note.group = 'test-group'
    note.save()
    assert list(Notification.list(user=user)) == [note]


@patch('plinth.notification.gettext')
def test_display_context(gettext, note, user, rf):
    """Test display context for a notification."""
    request = rf.get('/plinth/help/about/')

    data = {
        'test-key1': 'test-value1',
        'test-key2': 'translate:test-value2',
        'test-key3': {
            'test-key4': 'translate:test-value4',
            'test-key5': 'test-value5'
        }
    }
    expected_data = {
        'test-key1': 'test-value1',
        'test-key2': 'translated test-value2',
        'test-key3': {
            'test-key4': 'translated test-value4',
            'test-key5': 'test-value5'
        }
    }
    actions = [{'type': 'link', 'text': 'Test text', 'url': 'Test url'}]
    expected_actions = [{
        'type': 'link',
        'text': 'translated Test text',
        'url': 'Test url'
    }]
    gettext.side_effect = lambda string: 'translated ' + string

    note.severity = 'error'
    note.title = 'Test Title {test-key1}'
    note.message = 'Test message {test-key1}'
    note.actions = actions
    note.user = 'test-user'
    note.group = 'test-group'
    note.data = data
    note.save()

    context = Notification.get_display_context(request, user)
    assert len(context['notifications']) == 1
    assert context['max_severity'] == 'error'

    context_note = context['notifications'][0]
    assert context_note['id'] == 'test-notification'
    assert context_note['app_id'] == 'test-app'
    assert context_note['severity'] == 'error'
    assert context_note['title'] == 'translated Test Title test-value1'
    assert context_note['message'] == 'translated Test message test-value1'
    assert context_note['body'] is None
    assert context_note['actions'] == expected_actions
    assert context_note['data'] == expected_data
    assert note.data == data
    now = datetime.datetime.now(datetime.timezone.utc)
    assert (now - context_note['created_time']).seconds < 60
    assert (now - context_note['last_update_time']).seconds < 60
    assert context_note['user'] == 'test-user'
    assert context_note['group'] == 'test-group'
    assert not context_note['dismissed']


def test_display_context_body_template(note, user, load_cfg, rf):
    """Test display context for a notification with body template."""
    request = rf.get('/plinth/help/about/')

    note.body_template = 'invalid-template.html'
    note.save()

    context = Notification.get_display_context(request, user)
    assert context['notifications'][0]['body'] == {
        'content': b'Template invalid-template.html does not exist.'
    }

    note.body_template = 'test-notification.html'
    note.save()

    context = Notification.get_display_context(request, user)
    context_note = context['notifications'][0]
    assert context_note['body'].content == \
        b'Test notification body /plinth/help/about/\n'
