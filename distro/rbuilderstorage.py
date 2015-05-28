#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import os

from amiconfig.errors import *
from amiconfig.lib import util
from amiconfig.lib import spacedaemon
from amiconfig.plugin import AMIPlugin

class AMIConfigPlugin(AMIPlugin):
    name = 'rbuilderstorage'

    def configure(self):
        """
        [rbuilderstorage]
        # optional list of ':' seperated dirs
        relocate-paths = /srv:/var/rmake
        """

        try:
            blkdevmap = self.id.getBlockDeviceMapping()
        except EC2DataRetrievalError:
            return

        cfg = self.ud.getSection('storage')

        ephemeralDevs = []
        for key, dev in blkdevmap.iteritems():
            if 'ephemeral' in key:
                mntpnt = '/ephemeral/%s' % key[9:]
                # ephemeral device names are not correct
                # for our kernel
                if not os.path.exists('/dev/%s' % dev):
                    dev = dev.replace('sd', 'xvd')
                ephemeralDevs.append(('/dev/%s' % dev, mntpnt))

        relocatePaths = ['/srv', '/var/rmake']
        if 'relocate-paths' in cfg:
            relocatePaths = cfg['relocate-paths'].split(':')

        # First ephemeral is scratch
        scratchDev = ephemeralDevs[0][0]
        os.system('pvcreate %s' % scratchDev)
        os.system('vgcreate vg00 %s' % scratchDev)

        # Second dev is for mass storage
        (dev, mntpnt) = ephemeralDevs[1]
         
        util.mkdirChain(mntpnt)
        util.call(['mount', dev, mntpnt])

        for relocPath in relocatePaths: 
            if os.path.exists(relocPath) \
               and not os.path.islink(relocPath):
                util.movetree(relocPath, '%s/%s' % (mntpnt, relocPath))
                os.symlink('%s/%s' % (mntpnt, relocPath), relocPath)
