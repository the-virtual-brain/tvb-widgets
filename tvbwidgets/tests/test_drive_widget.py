# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import os

import pytest
from ebrains_drive.files import SeafFile, SeafDir
from ebrains_drive.repo import Repo

from tvbwidgets.core.auth import CLB_AUTH
from tvbwidgets.ui.drive_widget import DriveWidget
from tvbwidgets.ui.storage_widget import StorageWidget

DUMMY_FILENAME = '/dummy_file.txt'
DUMMY_DIR = '/dummy_dir'
DUMMY_CONTENT = "Dummy content"


class MockSeafFile(SeafFile):
    def get_content(self):
        return DUMMY_CONTENT


class MockSeafDir(SeafDir):
    def __init__(self, repo, path, object_id, obj_type, empty_dir=False):
        super().__init__(repo, path, object_id, obj_type)
        self.empty_dir = empty_dir

    def ls(self, entity_type=None, force_refresh=True):
        if self.empty_dir:
            return list()
        return [MockSeafFile(self.repo, DUMMY_FILENAME, 1, SeafFile),
                MockSeafDir(self.repo, DUMMY_DIR, 2, SeafDir, empty_dir=True)]


class MockRepo(Repo):

    def __init__(self, client, **kwargs):
        super(MockRepo, self).__init__(client, **kwargs)
        self.dir = MockSeafDir(self, '/', 1, SeafDir)

    def get_dir(self, path):
        if path == DriveWidget.ROOT:
            return self.dir
        return self.dir.ls()[1]

    def get_file(self, path):
        if path is None:
            return None
        return self.dir.ls()[0]


class MockRepos:

    def __init__(self, client):
        self.client = client

    def list_repos(self):
        return [MockRepo(self.client, name='repo1', id=1), MockRepo(self.client, name='repo2', id=2)]


class MockDriveClient:
    @property
    def repos(self):
        return MockRepos(self)


def test_drive_widget(mocker):
    def mockk(token):
        return MockDriveClient()

    mocker.patch('ebrains_drive.connect', mockk)

    if os.environ.get(CLB_AUTH):
        os.environ.pop(CLB_AUTH)

    with pytest.raises(RuntimeError):
        DriveWidget()

    os.environ[CLB_AUTH] = "test_auth_token"
    widget = DriveWidget()

    assert widget.get_chosen_repo() is None

    # this triggers the observe events on dropbox widget
    widget.repos_dropdown.value = widget.repos_dropdown.options['repo1']
    assert isinstance(widget.get_chosen_repo(), Repo)
    assert widget.get_selected_file_path() is None
    assert len(widget.files_list.options) == 3  # 3 because the parent dir is also added

    # this triggers the observe events on select widget
    widget.files_list.value = widget.files_list.options[1]
    assert widget.get_selected_file_path() == DUMMY_FILENAME
    assert widget.get_selected_file_content() == DUMMY_CONTENT

    # this triggers the observe events on select widget
    widget.files_list.value = widget.files_list.options[2]
    assert widget._parent_dir.path == '/'
    assert widget.get_selected_file_path() is None
    assert len(widget.files_list.options) == 1

    with pytest.raises(AttributeError):
        widget.get_selected_file_content()


def test_storage_widget(mocker):
    def mockk(token):
        return MockDriveClient()

    mocker.patch('ebrains_drive.connect', mockk)

    if os.environ.get(CLB_AUTH):
        os.environ.pop(CLB_AUTH)

    with pytest.raises(RuntimeError):
        StorageWidget()

    os.environ[CLB_AUTH] = "test_auth_token"
    widget = StorageWidget()

    widget.drive_api.repos_dropdown.value = widget.drive_api.repos_dropdown.options['repo1']
    widget.drive_api.files_list.value = widget.drive_api.files_list.options[1]

    assert widget.get_selected_file_name() == DUMMY_FILENAME
    assert widget.get_selected_file_content() == DUMMY_CONTENT
