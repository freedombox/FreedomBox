# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test scheduling of backups.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

import pytest

import plinth.modules.backups.repository as repository_module
from plinth.app import App

from ..components import BackupRestore
from ..schedule import Schedule


class AppTest(App):
    """Sample App for testing."""
    app_id = 'test-app'


def _get_backup_component(name):
    """Return a BackupRestore component."""
    return BackupRestore(name)


def _get_test_app(name):
    """Return an App."""
    app = AppTest()
    app.app_id = name
    app._all_apps[name] = app
    app.add(BackupRestore(name + '-component'))
    return app


def test_init_default_values():
    """Test initialization of schedule with default values."""
    schedule = Schedule('test-uuid')
    assert schedule.repository_uuid == 'test-uuid'
    assert not schedule.enabled
    assert schedule.daily_to_keep == 5
    assert schedule.weekly_to_keep == 3
    assert schedule.monthly_to_keep == 3
    assert schedule.run_at_hour == 2
    assert schedule.unselected_apps == []


def test_init():
    """Test initialization with explicit values."""
    schedule = Schedule('test-uuid', enabled=True, daily_to_keep=1,
                        weekly_to_keep=2, monthly_to_keep=5, run_at_hour=0,
                        unselected_apps=['test-app1', 'test-app2'])
    assert schedule.repository_uuid == 'test-uuid'
    assert schedule.enabled
    assert schedule.daily_to_keep == 1
    assert schedule.weekly_to_keep == 2
    assert schedule.monthly_to_keep == 5
    assert schedule.run_at_hour == 0
    assert schedule.unselected_apps == ['test-app1', 'test-app2']


def test_get_storage_format():
    """Test that storage format is properly returned."""
    schedule = Schedule('test-uuid', enabled=True, daily_to_keep=1,
                        weekly_to_keep=2, monthly_to_keep=5, run_at_hour=23,
                        unselected_apps=['test-app1', 'test-app2'])
    assert schedule.get_storage_format() == {
        'enabled': True,
        'daily_to_keep': 1,
        'weekly_to_keep': 2,
        'monthly_to_keep': 5,
        'run_at_hour': 23,
        'unselected_apps': ['test-app1', 'test-app2'],
    }


def _get_archives_from_test_data(data):
    """Return a list of archives from test data."""
    archives = []
    for index, item in enumerate(data):
        archive_time = item['time']
        if isinstance(archive_time, str):
            archive_time = datetime.strptime(archive_time,
                                             '%Y-%m-%d %H:%M:%S+0000')

        comment = json.dumps({'type': 'scheduled', 'periods': item['periods']})
        archive = {
            'comment': comment,
            'start': archive_time,
            'name': f'archive-{index}'
        }
        archives.append(archive)

    return archives


# - First item is the arguments to send construct Schedule()
# - Second item is the list of previous backups in the system.
# - Third item is the return value of datetime.datetime.now().
# - Fourth item is the list of periods for which backups must be triggered.
# - Fifth item is the list of expected archives to be deleted after backup.
cases = [
    # Schedule is disabled
    [
        [False, 10, 10, 10, 0],
        [],
        datetime(2021, 1, 1),
        [],
        [],
    ],
    # No past backups
    [
        [True, 10, 10, 10, 0],
        [],
        datetime(2021, 1, 1),
        ['daily', 'weekly', 'monthly'],
        [],
    ],
    # Daily backup taken recently
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['daily'],
            'time': datetime(2021, 1, 1) - timedelta(seconds=600)
        }],
        datetime(2021, 1, 1),
        [],
        [],
    ],
    # Weekly backup taken recently
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['weekly'],
            'time': datetime(2021, 1, 1) - timedelta(seconds=600)
        }],
        datetime(2021, 1, 1),
        [],
        [],
    ],
    # Monthly backup taken recently
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['monthly'],
            'time': datetime(2021, 1, 1) - timedelta(seconds=600)
        }],
        datetime(2021, 1, 1),
        [],
        [],
    ],
    # Backup taken not so recently
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['daily'],
            'time': datetime(2021, 1, 1) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 1),
        ['daily', 'weekly', 'monthly'],
        [],
    ],
    # Too long since a daily backup, not scheduled time
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['daily'],
            'time': datetime(2021, 1, 1) - timedelta(days=1, seconds=3601)
        }],
        datetime(2021, 1, 1),
        ['daily', 'weekly', 'monthly'],
        [],
    ],
    # No too long since a daily backup, not scheduled time
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['daily'],
            'time': datetime(2021, 1, 1) - timedelta(days=1, seconds=3600)
        }],
        datetime(2021, 1, 1),
        ['weekly', 'monthly'],
        [],
    ],
    # Too long since a weekly backup, not scheduled time
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['weekly'],
            'time': datetime(2021, 1, 1) - timedelta(days=7, seconds=3601)
        }],
        datetime(2021, 1, 1),
        ['daily', 'weekly', 'monthly'],
        [],
    ],
    # No too long since a daily backup, not scheduled time
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['weekly'],
            'time': datetime(2021, 1, 1) - timedelta(days=7, seconds=3600)
        }],
        datetime(2021, 1, 1),
        ['daily', 'monthly'],
        [],
    ],
    # Too long since a monthly backup, not scheduled time, year rounding
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['monthly'],
            'time': datetime(2020, 12, 1)
        }],
        datetime(2021, 1, 1, 1, 0, 1),
        ['daily', 'weekly', 'monthly'],
        [],
    ],
    # No too long since a monthly backup, not scheduled time, year rounding
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['monthly'],
            'time': datetime(2020, 12, 1)
        }],
        datetime(2021, 1, 1, 1),
        ['daily', 'weekly'],
        [],
    ],
    # Too long since a monthly backup, not scheduled time, no year rounding
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['monthly'],
            'time': datetime(2020, 11, 1)
        }],
        datetime(2020, 12, 1, 1, 0, 1),
        ['daily', 'weekly', 'monthly'],
        [],
    ],
    # No too long since a monthly backup, not scheduled time, no year rounding
    [
        [True, 10, 10, 10, 2],
        [{
            'periods': ['monthly'],
            'time': datetime(2020, 11, 1)
        }],
        datetime(2020, 12, 1, 1),
        ['daily', 'weekly'],
        [],
    ],
    # Time for daily backup
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['daily', 'weekly', 'monthly'],
            'time': datetime(2021, 1, 2) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 2),
        ['daily'],
        [],
    ],
    # Time for daily backup, different scheduled time
    [
        [True, 10, 10, 10, 11],
        [{
            'periods': ['daily', 'weekly', 'monthly'],
            'time': datetime(2021, 1, 2, 11) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 2, 11),
        ['daily'],
        [],
    ],
    # Time for daily/weekly backup, 2021-01-03 is a Sunday
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['daily', 'weekly', 'monthly'],
            'time': datetime(2021, 1, 3) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 3),
        ['daily', 'weekly'],
        [],
    ],
    # Time for daily/monthly backup
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['daily', 'weekly', 'monthly'],
            'time': datetime(2021, 1, 1) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 1),
        ['daily', 'monthly'],
        [],
    ],
    # Daily backups disabled by setting the no. of backups to keep to 0
    [
        [True, 0, 10, 10, 0],
        [],
        datetime(2021, 1, 1),
        ['weekly', 'monthly'],
        [],
    ],
    # Weekly backups disabled by setting the no. of backups to keep to 0
    [
        [True, 10, 0, 10, 0],
        [],
        datetime(2021, 1, 1),
        ['daily', 'monthly'],
        [],
    ],
    # Monthly backups disabled by setting the no. of backups to keep to 0
    [
        [True, 10, 10, 0, 0],
        [],
        datetime(2021, 1, 1),
        ['daily', 'weekly'],
        [],
    ],
    # Not scheduled, not too long since last, no backup necessary
    [
        [True, 10, 10, 10, 0],
        [{
            'periods': ['daily', 'weekly', 'monthly'],
            'time': datetime(2021, 1, 2, 1) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 2, 1),
        [],
        [],
    ],
    # Cleanup daily backups
    [
        [True, 2, 10, 10, 0],
        [{
            'periods': ['daily'],
            'time': datetime(2021, 1, 3, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily'],
            'time': datetime(2021, 1, 2, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily'],
            'time': datetime(2021, 1, 1, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily'],
            'time': datetime(2021, 1, 1, 0) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 4, 1),
        ['daily', 'weekly', 'monthly'],
        ['archive-2', 'archive-3'],
    ],
    # Cleanup weekly backups
    [
        [True, 10, 2, 10, 0],
        [{
            'periods': ['weekly'],
            'time': datetime(2021, 1, 3, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['weekly'],
            'time': datetime(2021, 1, 2, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['weekly'],
            'time': datetime(2021, 1, 1, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['weekly'],
            'time': datetime(2021, 1, 1, 0) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 4, 1),
        ['daily', 'monthly'],
        ['archive-2', 'archive-3'],
    ],
    # Cleanup monthly backups
    [
        [True, 10, 10, 2, 0],
        [{
            'periods': ['monthly'],
            'time': datetime(2021, 1, 3, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['monthly'],
            'time': datetime(2021, 1, 2, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['monthly'],
            'time': datetime(2021, 1, 1, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['monthly'],
            'time': datetime(2021, 1, 1, 0) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 4, 1),
        ['daily', 'weekly'],
        ['archive-2', 'archive-3'],
    ],
    # Cleanup daily backups, but keep due to them being weekly/monthly too
    [
        [True, 2, 1, 10, 0],
        [{
            'periods': ['daily'],
            'time': datetime(2021, 1, 6, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily'],
            'time': datetime(2021, 1, 5, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily', 'weekly'],
            'time': datetime(2021, 1, 4, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily', 'weekly'],
            'time': datetime(2021, 1, 3, 1) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily', 'monthly'],
            'time': datetime(2021, 1, 2, 0) - timedelta(seconds=3 * 3600)
        }, {
            'periods': ['daily'],
            'time': datetime(2021, 1, 1, 0) - timedelta(seconds=3 * 3600)
        }],
        datetime(2021, 1, 7, 1),
        ['daily'],
        ['archive-3', 'archive-5'],
    ],
]


@pytest.mark.parametrize(
    'schedule_params,archives_data,test_now,run_periods,cleanups', cases)
@patch('plinth.app.App.get_setup_state')
@patch('plinth.modules.backups.repository.get_instance')
def test_run_schedule(get_instance, get_setup_state, schedule_params,
                      archives_data, test_now, run_periods, cleanups):
    """Test that backups are run at expected time."""
    get_setup_state.return_value = App.SetupState.UP_TO_DATE

    repository = MagicMock()
    repository.list_archives.side_effect = \
        lambda: _get_archives_from_test_data(archives_data)
    get_instance.return_value = repository
    repository.generate_archive_name = lambda: \
        repository_module.BaseBorgRepository.generate_archive_name(None)

    with patch('plinth.modules.backups.schedule.datetime') as mock_datetime, \
         patch('plinth.modules.backups.repository.datetime') \
         as repo_datetime, patch('plinth.app.App.list') as app_list:
        app_list.return_value = [
            _get_test_app('test-app1'),
            _get_test_app('test-app2'),
            _get_test_app('test-app3')
        ]

        repo_datetime.datetime.now.return_value = test_now
        mock_datetime.now.return_value = test_now
        mock_datetime.strptime = datetime.strptime
        mock_datetime.min = datetime.min
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(
            *args, **kwargs)

        schedule = Schedule('test_uuid', schedule_params[0],
                            schedule_params[1], schedule_params[2],
                            schedule_params[3], schedule_params[4],
                            ['test-app2'])
        schedule.run_schedule()

        if not run_periods:
            repository.create_archive.assert_not_called()
        else:
            run_periods.sort()
            name = 'scheduled: {periods}: {datetime}'.format(
                periods=', '.join(run_periods),
                datetime=repo_datetime.datetime.now().astimezone().replace(
                    microsecond=0).isoformat())
            app_ids = ['test-app1', 'test-app3']
            archive_comment = json.dumps({
                'type': 'scheduled',
                'periods': run_periods
            }).replace('{', '{{').replace('}', '}}')
            repository.create_archive.assert_has_calls(
                [call(name, app_ids, archive_comment=archive_comment)])

        if not cleanups:
            repository.delete_archive.assert_not_called()
        else:
            calls = [call(name) for name in cleanups]
            repository.delete_archive.assert_has_calls(calls)
