# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

class WidgetsException(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = str(message)

    def __str__(self):
        return self.message


class InvalidInputException(WidgetsException):
    """
    To be thrown when an invalid input is received.
    """


class InvalidFileException(WidgetsException):
    """
    To be thrown if an invalid filename is used.
    """


class ModelNotFoundError(WidgetsException):
    """
    To be thrown when a model class can't be found or doesn't exist
    """


class ModelExporterNotFoundError(WidgetsException):
    """
    To be thrown when an attempt is being made to use an exporter that is not accessible
    """


class BucketDTOError(WidgetsException):
    """
    Exception on bucket DTOs
    """
