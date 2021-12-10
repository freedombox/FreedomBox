# SPDX-License-Identifier: AGPL-3.0-or-later
from django.urls import path
from stronghold.decorators import public

from plinth.utils import non_admin_view

from . import views

urlpatterns = [
    path('apps/email_server/', views.EmailServerView.as_view(), name='index'),
    path('apps/email_server/my_aliases',
         non_admin_view(views.AliasView.as_view()), name='aliases'),
    path('apps/email_server/config.xml', public(views.XmlView.as_view())),
]
