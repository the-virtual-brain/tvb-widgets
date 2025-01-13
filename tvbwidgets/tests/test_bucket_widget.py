# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#
import os

import pytest
from ebrains_drive.exceptions import Unauthorized
from tvbwidgets.core.auth import CLB_AUTH
from tvbwidgets.ui.bucket_widget import BucketWidget

DUMMY_CONTENT = b'test content'


class MockBucketDTO:
    def __init__(self, name, role='', is_public=True):
        self.name = name
        self.role = role
        self.is_public = is_public


class MockFile:
    def __init__(self, name):
        # type: (str) -> None
        self.name = name

    def get_content(self):
        return DUMMY_CONTENT

    def get_download_link(self):
        return ''


class MockBucket:
    def __init__(self, files_count=2, name='test_bucket', target='buckets', dataproxy_entity_name='test_bucket'):
        self.name = name
        self.files = [MockFile(f'file{number}') for number in range(files_count)]
        self.target = target
        self.dataproxy_entity_name = dataproxy_entity_name

    def ls(self, prefix=''):
        return [f for f in self.files if f.name.startswith(prefix)]


class MockBuckets:
    def __init__(self):
        self.buckets = {
            'test_bucket': MockBucket()
        }

    def get_bucket(self, name):
        try:
            return self.buckets[name]
        except KeyError:
            raise Unauthorized('Unauthorized in tests')

    def list_buckets(self):
        return [MockBucketDTO(b) for b in self.buckets.keys()]


class MockBucketApiClient:
    def __init__(self, token=''):
        self.token = token
        self.buckets = MockBuckets()


@pytest.fixture
def mock_client(mocker):
    return mocker.patch('tvbwidgets.ui.bucket_widget.ExtendedBucketApiClient', MockBucketApiClient)


@pytest.fixture
def mock_requests_get(mocker):
    mock_response = mocker.Mock()
    mock_response.content = DUMMY_CONTENT
    return mocker.patch('requests.get', return_value=mock_response)


def test_get_files_in_bucket(mock_client, mock_requests_get):
    """
    tests that client returns list of files from bucket
    """
    if os.environ.get(CLB_AUTH):
        os.environ.pop(CLB_AUTH)

    with pytest.raises(RuntimeError):
        BucketWidget()

    os.environ[CLB_AUTH] = "test_auth_token"
    widget = BucketWidget()

    # test observe event on buckets dropdown
    assert widget.buckets_dropdown.value is None
    assert widget.files_list.value is None
    assert len(widget.files_list.options) == 0
    widget.buckets_dropdown.value = widget.buckets_dropdown.options[0]
    assert len(widget.files_list.options) == 2
    widget.files_list.value = widget.files_list.options[0]

    # test BucketWidget functions
    assert widget.get_selected_file_path() == widget.buckets_dropdown.value + '/' + widget.files_list.value
    assert widget.get_selected_file_content() == DUMMY_CONTENT
