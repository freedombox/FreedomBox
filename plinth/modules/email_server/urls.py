# SPDX-License-Identifier: AGPL-3.0-or-later
from django.urls import path
from plinth.utils import non_admin_view
from . import views


urlpatterns = [
    path('apps/email_server/', views.EmailServerView.as_view(), name='index'),
    path('apps/email_server/my_aliases',
         non_admin_view(views.AliasView.as_view()), name='my_aliases')
]
