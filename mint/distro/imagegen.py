#
# Copyright (c) 2004-2005 Specifix, Inc.
#
# All Rights Reserved
#

class ImageGenerator:
    def __init__(self, client, cfg, job, profileId):
        self.client = client
        self.cfg = cfg
        self.job = job
        self.profileId = profileId

    def write(self):
        raise NotImplementedError
