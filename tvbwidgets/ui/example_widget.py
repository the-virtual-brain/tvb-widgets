#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

"""
Example widget with a front-end definition.

This represents the Widget linking a Model and a View.
"""

from ipywidgets import DOMWidget
from traitlets import Unicode
from .._version import __frontend_module__ as module_name, __version__ as module_version


class ExampleWidget(DOMWidget):
    _model_name = Unicode('ExampleModel').tag(sync=True)
    _model_module = Unicode(module_name).tag(sync=True)
    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_name = Unicode('ExampleView').tag(sync=True)
    _view_module = Unicode(module_name).tag(sync=True)
    _view_module_version = Unicode(module_version).tag(sync=True)

    value = Unicode('Hello World').tag(sync=True)
