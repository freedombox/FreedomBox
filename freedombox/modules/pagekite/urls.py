# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the PageKite module
"""

from django.urls import re_path

from .views import AddCustomServiceView, ConfigurationView, DeleteServiceView

urlpatterns = [
    re_path(r'^sys/pagekite/$', ConfigurationView.as_view(), name='index'),
    re_path(r'^sys/pagekite/services/custom/add/$',
            AddCustomServiceView.as_view(), name='add-custom-service'),
    re_path(r'^sys/pagekite/services/custom/delete/$',
            DeleteServiceView.as_view(), name='delete-custom-service'),
]
