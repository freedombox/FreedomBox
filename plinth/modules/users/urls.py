# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Users module
"""

from django.urls import re_path
from stronghold.decorators import public

from plinth.utils import non_admin_view

from . import views

urlpatterns = [
    re_path(r'^sys/users/$', views.UserList.as_view(), name='index'),
    re_path(r'^sys/users/create/$', views.UserCreate.as_view(), name='create'),
    re_path(r'^sys/users/(?P<slug>[\w.@+-]+)/edit/$',
            non_admin_view(views.UserUpdate.as_view()), name='edit'),
    re_path(r'^sys/users/(?P<slug>[\w.@+-]+)/change_password/$',
            non_admin_view(views.UserChangePassword.as_view()),
            name='change_password'),
    re_path(r'^accounts/login/$', public(views.LoginView.as_view()),
            name='login'),
    re_path(r'^accounts/logout/$', public(views.logout), name='logout'),
    re_path(r'^users/firstboot/$', public(views.FirstBootView.as_view()),
            name='firstboot'),
    re_path(r'accounts/login/locked/$', public(views.CaptchaView.as_view()),
            name='locked_out'),
]
