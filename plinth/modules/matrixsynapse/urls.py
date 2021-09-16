# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the matrix-synapse module.
"""

from django.urls import re_path

from .views import MatrixSynapseAppView, SetupView

urlpatterns = [
    re_path(r'^apps/matrixsynapse/setup/$', SetupView.as_view(), name='setup'),
    re_path(r'^apps/matrixsynapse/$', MatrixSynapseAppView.as_view(),
            name='index'),
]
