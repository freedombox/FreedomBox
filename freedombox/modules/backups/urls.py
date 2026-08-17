# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the backups module.
"""

from django.urls import re_path

from .views import (AddRemoteRepositoryView, AddRepositoryView, BackupsView,
                    CreateArchiveView, DeleteArchiveView, DownloadArchiveView,
                    RemoveRepositoryView, RestoreArchiveView,
                    RestoreFromUploadView, ScheduleView, UploadArchiveView,
                    VerifySshHostkeyView, mount_repository, umount_repository)

urlpatterns = [
    re_path(r'^sys/backups/$', BackupsView.as_view(), name='index'),
    re_path(r'^sys/backups/(?P<uuid>[^/]+)/schedule/$', ScheduleView.as_view(),
            name='schedule'),
    re_path(r'^sys/backups/create/(?:(?P<app_id>[1-9a-z\-_]+)/)?$',
            CreateArchiveView.as_view(), name='create'),
    re_path(r'^sys/backups/(?P<uuid>[^/]+)/download/(?P<name>[^/]+)/$',
            DownloadArchiveView.as_view(), name='download'),
    re_path(r'^sys/backups/(?P<uuid>[^/]+)/delete/(?P<name>[^/]+)/$',
            DeleteArchiveView.as_view(), name='delete'),
    re_path(r'^sys/backups/upload/$', UploadArchiveView.as_view(),
            name='upload'),
    re_path(r'^sys/backups/(?P<uuid>[^/]+)/restore-archive/(?P<name>[^/]+)/$',
            RestoreArchiveView.as_view(), name='restore-archive'),
    re_path(r'^sys/backups/restore-from-upload/$',
            RestoreFromUploadView.as_view(), name='restore-from-upload'),
    re_path(r'^sys/backups/repositories/add/$', AddRepositoryView.as_view(),
            name='add-repository'),
    re_path(r'^sys/backups/repositories/add-remote/$',
            AddRemoteRepositoryView.as_view(), name='add-remote-repository'),
    re_path(r'^sys/backups/repositories/(?P<uuid>[^/]+)/ssh-verify/$',
            VerifySshHostkeyView.as_view(), name='verify-ssh-hostkey'),
    re_path(r'^sys/backups/repositories/(?P<uuid>[^/]+)/delete/$',
            RemoveRepositoryView.as_view(), name='repository-remove'),
    re_path(r'^sys/backups/repositories/(?P<uuid>[^/]+)/mount/$',
            mount_repository, name='repository-mount'),
    re_path(r'^sys/backups/repositories/(?P<uuid>[^/]+)/umount/$',
            umount_repository, name='repository-umount'),
]
