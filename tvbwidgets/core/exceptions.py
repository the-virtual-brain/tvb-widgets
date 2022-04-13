# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2023, TVB Widgets Team
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
