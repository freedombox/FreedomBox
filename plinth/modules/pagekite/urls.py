# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the PageKite module
"""

from django.conf.urls import url

from .views import AddCustomServiceView, ConfigurationView, DeleteServiceView

urlpatterns = [
    url(r'^sys/pagekite/$', ConfigurationView.as_view(), name='index'),
    url(r'^sys/pagekite/services/custom/add/$', AddCustomServiceView.as_view(),
        name='add-custom-service'),
    url(r'^sys/pagekite/services/custom/delete/$', DeleteServiceView.as_view(),
        name='delete-custom-service'),
]
