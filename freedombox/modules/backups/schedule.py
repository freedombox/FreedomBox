# SPDX-License-Identifier: AGPL-3.0-or-later
"""Schedule for automatic backups.

Every day automatic backups are triggered. Daily, weekly and monthly backups
are taken. Cleanup of old backups is triggered and specified number of backups
are kept back in each category.

"""

import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class Schedule:
    """Description of a schedule for backups."""

    def __init__(self, repository_uuid, enabled=None, daily_to_keep=None,
                 weekly_to_keep=None, monthly_to_keep=None, run_at_hour=None,
                 unselected_apps=None):
        """Initialize the schedule object instance.

        'repository_uuid' is the unique ID of the repository that this
        schedule is applied to.

        'enabled' is a boolean indicating whether scheduled backups are enabled
        or disabled.

        'daily_to_keep' is a whole number indicating the number of daily
        backups to keep. Older backups are removed after creating a new backup
        to keep these many backups. A value of 0 means no such backups are
        scheduled.

        'weekly_to_keep' is a whole number indicating the number of weekly
        backups to keep. Older backups are removed after creating a new backup
        to keep these many backups. A value of 0 means no such backups are
        scheduled.

        'monthly_to_keep' is a whole number indicating the number of monthly
        backups to keep. Older backups are removed after creating a new backup
        to keep these many backups. A value of 0 means no such backups are
        scheduled.

        'run_at_hour' is a whole number indicating the hour of the day when the
        backups must be scheduled.

        'unselected_apps' is a list of app IDs that should not be included when
        scheduling backups. A negative list is maintained because when a new
        app is installed, it is included into the schedule by default unless
        explicitly removed. This is the safer option.

        """
        self.repository_uuid = repository_uuid
        self.enabled = enabled or False
        self.daily_to_keep = daily_to_keep if daily_to_keep is not None else 5
        self.weekly_to_keep = weekly_to_keep if weekly_to_keep is not None \
            else 3
        self.monthly_to_keep = monthly_to_keep if monthly_to_keep is not None \
            else 3
        # Run at 02:00 by default everyday
        self.run_at_hour = run_at_hour if run_at_hour is not None else 2
        self.unselected_apps = unselected_apps or []

    def get_storage_format(self):
        """Return the object serialized as dict suitable for instantiation."""
        return {
            'enabled': self.enabled,
            'daily_to_keep': self.daily_to_keep,
            'weekly_to_keep': self.weekly_to_keep,
            'monthly_to_keep': self.monthly_to_keep,
            'run_at_hour': self.run_at_hour,
            'unselected_apps': self.unselected_apps,
        }

    @staticmethod
    def _is_backup_too_soon(recent_backup_times):
        """Return whether a backup was already taken recently."""
        now = datetime.now()
        if now - recent_backup_times['daily'] < timedelta(seconds=2 * 3600):
            return True

        if now - recent_backup_times['weekly'] < timedelta(seconds=2 * 3600):
            return True

        if now - recent_backup_times['monthly'] < timedelta(seconds=2 * 3600):
            return True

        return False

    @staticmethod
    def _too_long_since_last_backup(recent_backup_times):
        """Return periods for which it has been too long since last backup."""
        periods = []
        local_time = datetime.now()

        if local_time - recent_backup_times['daily'] > timedelta(
                days=1, seconds=3600):
            periods.append('daily')

        if local_time - recent_backup_times['weekly'] > timedelta(
                days=7, seconds=3600):
            periods.append('weekly')

        last_monthly = recent_backup_times['monthly']
        try:
            next_monthly = last_monthly.replace(month=last_monthly.month + 1)
        except ValueError:
            next_monthly = last_monthly.replace(month=1,
                                                year=last_monthly.year + 1)
        if local_time > next_monthly + timedelta(seconds=3600):
            periods.append('monthly')

        return periods

    def _time_for_periods(self):
        """Return periods for which it is scheduled time for backup."""
        periods = []
        local_time = datetime.now()

        if local_time.hour == self.run_at_hour:
            periods.append('daily')  # At specified hour

        if local_time.hour == self.run_at_hour and local_time.isoweekday(
        ) == 7:
            periods.append('weekly')  # At specified hour on Sunday

        if local_time.hour == self.run_at_hour and local_time.day == 1:
            periods.append('monthly')  # At specified hour on 1st of the month

        return periods

    def _get_disabled_periods(self):
        """Return the list of periods for which backup are disabled."""
        periods = []
        if self.daily_to_keep == 0:
            periods.append('daily')

        if self.weekly_to_keep == 0:
            periods.append('weekly')

        if self.monthly_to_keep == 0:
            periods.append('monthly')

        return periods

    def run_schedule(self):
        """Return scheduled backups, throw exception on failure.

        Frequent triggering: If the method is triggered too frequently for any
        reason, later triggers will not result in more backups as the previous
        backup has to be more than 2 hours old at least to trigger a new
        backup.

        Daemon offline: When the daemon is offline, no backups will be made.
        However, an hour after it is back online, backup check will be done and
        if it is determined that too much time has passed since the last
        backup, a new backup will be taken.

        Errors: When an error occurs during backup process, the method raises
        an exception. An hour later, it is triggered again. This time it will
        determine that too much time has passed since the last backup and will
        attempt to backup again. During a day about 24 attempts to backup will
        be made and reported. A backup may made at an unscheduled time due to
        this. This won't prevent the next backup from happening at the
        scheduled time (unless it is too close to the previous successful one).

        Clock changes: When the clock changes and is set forward, within an
        hour of the change, the schedule check will determine that it has been
        too long since the last backup and the backup will be triggered. This
        will result in a backup at an unscheduled time. When the clock changes
        and is set backward, it will result all previous backup that are more
        recent and current time being ignored for scheduling. Backups will be
        scheduled on time and error handling works.

        Day light saving time: When gaining an hour, it is possible that
        schedule qualifies a second time during a day for backup. This is
        avoided by checking if the backup is too soon since the earlier one.
        When loosing an hour, the schedule may not quality for backup on that
        day at all. However, an hour after scheduled time, it will deemed that
        too much time has passed since the previous backup and a backup will be
        scheduled.

        """
        if not self.enabled:
            return False

        repository = self._get_repository()
        repository.prepare()

        recent_backup_times = self._get_recent_backup_times(repository)
        if self._is_backup_too_soon(recent_backup_times):
            return False

        too_long_periods = self._too_long_since_last_backup(
            recent_backup_times)
        time_for_periods = self._time_for_periods()
        disabled_periods = self._get_disabled_periods()
        periods = set(too_long_periods).union(time_for_periods)
        periods = periods.difference(disabled_periods)
        if not periods:
            return False

        self._run_backup(periods)
        self._run_cleanup(repository)
        return True

    def _get_repository(self):
        """Return the repository to which this schedule is assigned."""
        from . import repository as repository_module
        return repository_module.get_instance(self.repository_uuid)

    @staticmethod
    def _serialize_comment(data):
        """Represent dictionary data as comment.

        Borg substitutes python like placeholders with {}.

        """
        comment = json.dumps(data)
        return comment.replace('{', '{{').replace('}', '}}')

    @staticmethod
    def _list_scheduled_archives(repository):
        """Return a list of archives due to scheduled backups."""
        now = datetime.now()

        archives = repository.list_archives()
        scheduled_archives = []
        for archive in archives:

            try:
                comment = json.loads(archive['comment'])
            except json.decoder.JSONDecodeError:
                continue

            if not isinstance(comment, dict) or \
               comment.get('type') != 'scheduled' or \
               not isinstance(comment.get('periods'), list):
                continue

            archive['comment'] = comment

            if archive['start'] > now:
                # This backup was taken when clock was set in future. Ignore it
                # to ensure backups continue to be taken.
                continue

            scheduled_archives.append(archive)

        return scheduled_archives

    def _get_recent_backup_times(self, repository):
        """Get the time since most recent daily, weekly and monthly backups."""
        times = {
            'daily': datetime.min,
            'weekly': datetime.min,
            'monthly': datetime.min
        }

        archives = self._list_scheduled_archives(repository)
        for archive in archives:
            periods = {'daily', 'weekly', 'monthly'}
            periods = periods.intersection(archive['comment']['periods'])
            for period in periods:
                if times[period] < archive['start']:
                    times[period] = archive['start']

        return times

    def _run_backup(self, periods):
        """Run a backup and mark it for given period."""
        logger.info('Running backup for repository %s, periods %s',
                    self.repository_uuid, periods)

        repository = self._get_repository()

        from . import api
        periods = list(periods)
        periods.sort()
        name = 'scheduled: {periods}: {name}'.format(
            periods=', '.join(periods),
            name=repository.generate_archive_name())
        comment = self._serialize_comment({
            'type': 'scheduled',
            'periods': periods
        })
        app_ids = [
            component.app_id
            for component in api.get_all_components_for_backup()
            if component.app_id not in self.unselected_apps
        ]

        repository.create_archive(name, app_ids, archive_comment=comment)

    def _run_cleanup(self, repository):
        """Cleanup old backups."""
        archives = self._list_scheduled_archives(repository)
        counts = {'daily': 0, 'weekly': 0, 'monthly': 0}
        for archive in archives:
            keep = False
            archive_periods = archive['comment']['periods']
            for period in set(counts).intersection(archive_periods):
                counts[period] += 1

                if period == 'daily' and counts[period] <= self.daily_to_keep:
                    keep = True

                if period == 'weekly' and \
                   counts[period] <= self.weekly_to_keep:
                    keep = True

                if period == 'monthly' and \
                   counts[period] <= self.monthly_to_keep:
                    keep = True

            if not keep:
                logger.info('Cleaning up in repository %s backup archive %s',
                            self.repository_uuid, archive['name'])
                repository.delete_archive(archive['name'])

        repository.cleanup()
