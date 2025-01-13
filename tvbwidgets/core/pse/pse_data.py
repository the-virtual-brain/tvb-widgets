# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from tvb.basic.neotraits.api import NArray, HasTraits, Attr
from tvb.core.neotraits.h5 import H5File, DataSet, Scalar, Json


class PSEData(HasTraits):
    x_title = Attr(str)
    y_title = Attr(str)
    x_value = Attr(list)
    y_value = Attr(list)
    metrics_names = Attr(list)
    results = NArray()


class PSEStorage(H5File):
    def __init__(self, path):
        super(PSEStorage, self).__init__(path)
        self.x_title = Scalar(PSEData.x_title, self)
        self.y_title = Scalar(PSEData.y_title, self)
        self.x_value = Json(PSEData.x_value, self)
        self.y_value = Json(PSEData.y_value, self)
        self.metrics_names = Json(PSEData.metrics_names, self)
        self.results = DataSet(PSEData.results, self)
