# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import configparser
from collections import OrderedDict


def parse_ini_file(ini_file):
    # type: (str) -> OrderedDict
    """
    :param ini_file: Valid file path towards an ini file
    :return: Dictionary after parsing
    """
    config = configparser.ConfigParser()
    config.read(filenames=ini_file, encoding='UTF-8')
    sections = config.sections()
    result = OrderedDict()
    for s in sections:
        result[s] = " "
        keys = config[s]
        for key in keys:
            result[key] = config[s][key]
    return result
