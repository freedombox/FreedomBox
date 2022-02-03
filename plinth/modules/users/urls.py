# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the Users module
"""

from axes.decorators import axes_dispatch
from django.urls import re_path
from stronghold.decorators import public

from plinth.modules.sso.views import CaptchaLoginView, SSOLoginView, logout
from plinth.utils import non_admin_view

from . import views

urlpatterns = [
    re_path(r'^sys/users/$', views.UserList.as_view(), name='index'),
    re_path(r'^sys/users/create/$', views.UserCreate.as_view(), name='create'),
    re_path(r'^sys/users/(?P<slug>[\w.@+-]+)/edit/$',
            non_admin_view(views.UserUpdate.as_view()), name='edit'),
    re_path(r'^sys/users/(?P<slug>[\w.@+-]+)/delete/$',
            views.UserDelete.as_view(), name='delete'),
    re_path(r'^sys/users/(?P<slug>[\w.@+-]+)/change_password/$',
            non_admin_view(views.UserChangePassword.as_view()),
            name='change_password'),

    # Authnz is handled by SSO

    # XXX: Use axes authentication backend and middleware instead of
    # axes_dispatch after axes 5.x becomes available in Debian stable.
    re_path(r'^accounts/login/$',
            public(axes_dispatch(SSOLoginView.as_view())), name='login'),
    re_path(r'^accounts/logout/$', public(logout), name='logout'),
    re_path(r'^users/firstboot/$', public(views.FirstBootView.as_view()),
            name='firstboot'),
    re_path(r'accounts/login/locked/$', public(CaptchaLoginView.as_view()),
            name='locked_out'),
]
