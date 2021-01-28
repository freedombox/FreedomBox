# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the backups module.
"""

from django.conf.urls import url

from .views import (AddRemoteRepositoryView, AddRepositoryView,
                    CreateArchiveView, DeleteArchiveView, DownloadArchiveView,
                    IndexView, RemoveRepositoryView, RestoreArchiveView,
                    RestoreFromUploadView, ScheduleView, UploadArchiveView,
                    VerifySshHostkeyView, mount_repository, umount_repository)

urlpatterns = [
    url(r'^sys/backups/$', IndexView.as_view(), name='index'),
    url(r'^sys/backups/(?P<uuid>[^/]+)/schedule/$', ScheduleView.as_view(),
        name='schedule'),
    url(r'^sys/backups/create/$', CreateArchiveView.as_view(), name='create'),
    url(r'^sys/backups/(?P<uuid>[^/]+)/download/(?P<name>[^/]+)/$',
        DownloadArchiveView.as_view(), name='download'),
    url(r'^sys/backups/(?P<uuid>[^/]+)/delete/(?P<name>[^/]+)/$',
        DeleteArchiveView.as_view(), name='delete'),
    url(r'^sys/backups/upload/$', UploadArchiveView.as_view(), name='upload'),
    url(r'^sys/backups/(?P<uuid>[^/]+)/restore-archive/(?P<name>[^/]+)/$',
        RestoreArchiveView.as_view(), name='restore-archive'),
    url(r'^sys/backups/restore-from-upload/$', RestoreFromUploadView.as_view(),
        name='restore-from-upload'),
    url(r'^sys/backups/repositories/add/$', AddRepositoryView.as_view(),
        name='add-repository'),
    url(r'^sys/backups/repositories/add-remote/$',
        AddRemoteRepositoryView.as_view(), name='add-remote-repository'),
    url(r'^sys/backups/repositories/(?P<uuid>[^/]+)/ssh-verify/$',
        VerifySshHostkeyView.as_view(), name='verify-ssh-hostkey'),
    url(r'^sys/backups/repositories/(?P<uuid>[^/]+)/delete/$',
        RemoveRepositoryView.as_view(), name='repository-remove'),
    url(r'^sys/backups/repositories/(?P<uuid>[^/]+)/mount/$', mount_repository,
        name='repository-mount'),
    url(r'^sys/backups/repositories/(?P<uuid>[^/]+)/umount/$',
        umount_repository, name='repository-umount'),
]
