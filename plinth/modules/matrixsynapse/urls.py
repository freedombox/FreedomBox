# SPDX-License-Identifier: AGPL-3.0-or-later
"""
URLs for the matrix-synapse module.
"""

from django.conf.urls import url

from .views import MatrixSynapseAppView, SetupView

urlpatterns = [
    url(r'^apps/matrixsynapse/setup/$', SetupView.as_view(), name='setup'),
    url(r'^apps/matrixsynapse/$', MatrixSynapseAppView.as_view(),
        name='index'),
]
