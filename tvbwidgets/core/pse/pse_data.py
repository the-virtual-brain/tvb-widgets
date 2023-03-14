# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

import numpy as np
from tvb.basic.neotraits.api import NArray, HasTraits, Range, List, Attr
from tvb.core.neotraits.h5 import H5File, DataSet, Scalar, JsonRange


class PSEData(HasTraits):
    x_title = Attr(str)
    y_title = Attr(str)
    # x_value = Range()
    # y_value = Range()
    # metrics_names = List(str)
    results = NArray()


class PSEStorage(H5File):
    def __init__(self, path):
        super(PSEStorage, self).__init__(path)
        self.x_title = Scalar(PSEData.x_title, self)
        self.y_title = Scalar(PSEData.y_title, self)
        # self.x_value = JsonRange(PSEData.x_value, self)
        # self.y_value = JsonRange(PSEData.y_value, self)
        # self.metrics_names = DataSet(PSEData.metrics_names, self)
        self.results = DataSet(PSEData.results, self)


pse_result = PSEData()
pse_result.x_title = "coupling"
pse_result.y_title = "speed"
pse_result.results = np.array((5, 10, 10))

f = PSEStorage("path.h5")
f.store(pse_result)
f.close()

pse_result2 = PSEData()
PSEStorage("path.h5").load_into(pse_result2)
print(pse_result2)
