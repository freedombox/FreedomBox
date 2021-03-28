# SPDX-License-Identifier: AGPL-3.0-or-later
from django.urls import path
from . import views


urlpatterns = [
    path('apps/email_server/', views.EmailServerView.as_view(), name='index')
]
