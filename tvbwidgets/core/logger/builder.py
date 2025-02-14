# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import os
import inspect
import weakref
import logging
import logging.config


class LoggerBuilder(object):
    """
    Class taking care of uniform Python logger initialization.
    It uses the Python native logging package.
    It's purpose is just to offer a common mechanism for initializing all modules in a package.
    """

    def __init__(self, config_file_name='logging.conf'):
        """
        Prepare Python logger based on a configuration file.
        :param: config_file_name - name of the logging configuration relative to the current package
        """
        current_folder = os.path.dirname(inspect.getfile(self.__class__))
        config_file_path = os.path.join(current_folder, config_file_name)

        home_directory = os.path.expanduser('~')
        log_file_path = os.path.join(home_directory, '.tvbwidgets.log')

        logging.config.fileConfig(config_file_path, disable_existing_loggers=False, defaults={'logfilename': log_file_path})
        self._loggers = weakref.WeakValueDictionary()

    def build_logger(self, parent_module):
        """
        Build a logger instance and return it
        """
        self._loggers[parent_module] = logger = logging.getLogger(parent_module)
        return logger

    def set_loggers_level(self, level):
        for logger in self._loggers.values():
            logger.setLevel(level)


# We make sure a single instance of logger-builder is created.
GLOBAL_LOGGER_BUILDER = LoggerBuilder()


def get_logger(parent_module=''):
    """
    Function to retrieve a new Python logger instance for current module.

    :param parent_module: module name for which to create logger.
    """
    return GLOBAL_LOGGER_BUILDER.build_logger(parent_module)
