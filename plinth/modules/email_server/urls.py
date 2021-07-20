# SPDX-License-Identifier: AGPL-3.0-or-later
from django.urls import path
from plinth.utils import non_admin_view
from . import views


urlpatterns = [
    path('apps/email_server/', views.EmailServerView.as_view(), name='index'),
    path('apps/email_server/security', views.TLSView.as_view()),

    path('apps/email_server/my_mail',
         non_admin_view(views.MyMailView.as_view()), name='my_mail'),
    path('apps/email_server/my_aliases',
         non_admin_view(views.AliasView.as_view())),
]
