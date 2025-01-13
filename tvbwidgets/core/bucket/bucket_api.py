# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

from ebrains_drive import BucketApiClient
from tvbwidgets.core.bucket.buckets import ExtendedBuckets


class ExtendedBucketApiClient(BucketApiClient):

    def __init__(self, username=None, password=None, token=None, env="") -> None:
        super().__init__(username, password, token, env)
        self.buckets = ExtendedBuckets(self)
