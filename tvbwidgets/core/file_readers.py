# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
#

from io import StringIO, BytesIO
import numpy
from tvb.basic.readers import ZipReader
from tvb.datatypes.connectivity import Connectivity
from tvb.datatypes.sensors import Sensors
from tvb.datatypes.surfaces import Surface


class TXTReader(object):

    def __read_bytes(self, content, type, use_cols=None):
        content_str = StringIO(content.decode())
        content_array = numpy.loadtxt(content_str, dtype=type, skiprows=0, usecols=use_cols)
        return content_array

    def read_floats(self, content, use_cols=None):
        return self.__read_bytes(content, type=numpy.float64, use_cols=use_cols)

    def read_ints(self, content):
        return self.__read_bytes(content, type=numpy.int64)

    def read_text(self, content, use_cols=None):
        return self.__read_bytes(content, type=numpy.str, use_cols=use_cols)


class DatatypeReader(object):

    def read_surface_from_zip_bytes(self, content_bytes):
        reader = ZipReader(BytesIO(content_bytes))

        # TODO: duplicated from tvb-library
        result = Surface()
        result.vertices = reader.read_array_from_file("vertices.txt")
        result.vertex_normals = reader.read_array_from_file("normals.txt")
        result.triangles = reader.read_array_from_file("triangles.txt", dtype=numpy.int32)
        result.configure()

        return result

    def read_sensors_from_txt_bytes(self, content_bytes):
        reader = TXTReader()

        result = Sensors()
        result.labels = reader.read_text(content_bytes, use_cols=(0,))
        result.locations = reader.read_floats(content_bytes, use_cols=(1, 2, 3))
        result.configure()

        return result

    def read_connectivity_from_zip_bytes(self, content_bytes):
        reader = ZipReader(BytesIO(content_bytes))

        # TODO: duplicated from tvb-library
        result = Connectivity()
        result.weights = reader.read_array_from_file("weights")
        if reader.has_file_like("centres"):
            result.centres = reader.read_array_from_file("centres", use_cols=(1, 2, 3))
            result.region_labels = reader.read_array_from_file("centres", dtype=numpy.str, use_cols=(0,))
        else:
            result.centres = reader.read_array_from_file("centers", use_cols=(1, 2, 3))
            result.region_labels = reader.read_array_from_file("centers", dtype=numpy.str, use_cols=(0,))
        result.orientations = reader.read_optional_array_from_file("average_orientations")
        result.cortical = reader.read_optional_array_from_file("cortical", dtype=numpy.bool)
        result.hemispheres = reader.read_optional_array_from_file("hemispheres", dtype=numpy.bool)
        result.areas = reader.read_optional_array_from_file("areas")
        result.tract_lengths = reader.read_array_from_file("tract_lengths")
        result.configure()

        return result
