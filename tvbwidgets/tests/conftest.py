# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2026, TVB Widgets Team
#

from unittest import mock

import pytest


@pytest.fixture
def mocker():
    """Small pytest-mock compatible fixture for this test suite."""

    class Mocker:
        Mock = mock.Mock
        MagicMock = mock.MagicMock

        def __init__(self):
            self._patchers = []

        def patch(self, *args, **kwargs):
            patcher = mock.patch(*args, **kwargs)
            patched = patcher.start()
            self._patchers.append(patcher)
            return patched

        def stopall(self):
            for patcher in reversed(self._patchers):
                patcher.stop()
            self._patchers = []

    mocker_fixture = Mocker()
    yield mocker_fixture
    mocker_fixture.stopall()
