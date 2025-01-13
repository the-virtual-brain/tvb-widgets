# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from dataclasses import dataclass
from typing import List
from ebrains_drive.buckets import Buckets
from tvbwidgets.core.exceptions import BucketDTOError
from tvbwidgets.core.logger.builder import get_logger

LOGGER = get_logger(__name__)


@dataclass
class BucketDTO:
    name: str
    role: str
    is_public: bool


class ExtendedBuckets(Buckets):
    BUCKETS_ENDPOINT = '/v1/buckets'

    def __init__(self, client):
        super().__init__(client)
        self._available_buckets: List[BucketDTO] = []

    def list_buckets(self):
        # type: () -> List[BucketDTO]
        """
        Queries the buckets endpoint for the available buckets for current user
        """
        try:
            resp = self.client.get(self.BUCKETS_ENDPOINT)
            json_resp = resp.json()
            updated_available_buckets = []
            for obj in json_resp:
                updated_available_buckets.append(BucketDTO(**obj))
            self._available_buckets = updated_available_buckets
            return self._available_buckets
        except KeyError as e:
            LOGGER.error(f'Received unexpected Bucket structure! {str(e)}')
            raise BucketDTOError('Unexpected response structure from server!')
