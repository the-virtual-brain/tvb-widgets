# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import bz2
import ipywidgets
from tvb.basic.readers import ReaderException

from tvbwidgets.core.exceptions import InvalidFileException
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets.ui.storage_widget import StorageWidget


class TVBWidgetWithBrowser(TVBWidget):
    MSG_TEMPLATE = '<span style="color:{1};">{0}</span>'
    MSG_COLOR = 'red'

    def __init__(self, collab=None, folder=None, selected_storage=0):
        super().__init__()
        self.storage_widget = StorageWidget(collab, folder, selected_storage)
        self.message_label = ipywidgets.HTML(layout=ipywidgets.Layout(height='25px'))

    def __display_message(self, msg):
        self.message_label.value = self.MSG_TEMPLATE.format(msg, self.MSG_COLOR)

    def __validate_file(self, file_name, accepted_suffix):
        if file_name is None:
            raise InvalidFileException("Please select a file!")

        for suffix in accepted_suffix:
            if file_name.endswith(suffix):
                return suffix
        raise InvalidFileException(
            f"Only {' or '.join(ext for ext in accepted_suffix)} files are supported for this data type!")

    def load_selected_file(self, datatype_cls, accepted_suffix=('.zip',)):
        file_name = self.storage_widget.get_selected_file_name()
        msg = ''
        self.logger.info(f"{file_name}")

        try:
            content_type = self.__validate_file(file_name, accepted_suffix)
        except InvalidFileException as e:
            msg = e.message
            self.logger.error(f"{e}")
            return
        finally:
            self.__display_message(msg)

        content_bytes = self.storage_widget.get_selected_file_content()

        try:
            datatype = datatype_cls.from_bytes_stream(content_bytes, content_type)
            datatype.configure()
            self.add_datatype(datatype)
        except ReaderException as e:
            msg = "The selected file does not contain all necessary data to load this data type! Please check the logs!"
            self.logger.error(f"{e}")
            return
        except Exception as e:
            msg = "Could not load data from this file! Please check the logs!"
            self.logger.error(f"{e}")
            return
        finally:
            self.__display_message(msg)
