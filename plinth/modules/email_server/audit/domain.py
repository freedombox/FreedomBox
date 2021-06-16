"""The domain audit resource"""
# SPDX-License-Identifier: AGPL-3.0-or-later

from . import models


def get():
    # Stub
    return models.Result('Email domains')


def repair():
    # Stub
    raise RuntimeError()
