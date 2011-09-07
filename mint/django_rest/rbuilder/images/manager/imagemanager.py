#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import logging
#from mint.django_rest.rbuilder.images import models
import exceptions
from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.images import models

log = logging.getLogger(__name__)
exposed = basemanager.exposed

# this is the order originally presented in the UI when hard coded
# there.  We may wish to change sorting
IMAGE_TYPES = [
    [ 'vmware',        'VMware(R) Virtual Appliance'               ],
    [ 'appliance_iso', 'Appliance Installable ISO'                 ],
    [ 'update_cd_dvd', 'Update CD/DVD'                             ],
    [ 'online_update', 'Online Update'                             ],
    [ 'xen',           'Citrix(R) XenServer(TM) Appliance'         ],
    [ 'ec2',           'Amazon Machine Image (EC2)'                ],
    [ 'tar',           'Tar File'                                  ],
    [ 'eucalyptus',    'Eucalyptus/Mountable File System'          ],
    [ 'vmware_esx',    'VMware(R) ESX(R) Server Virtual Appliance' ],
    [ 'raw',           'KVM/Parallels/QEMU/Raw Hard Disk'          ]
]

IMAGE_ARCHES = [
    'x86', 'x86_64'
]

class ImageManager(basemanager.BaseManager):
    pass

    @exposed
    def getImageDefinitionDescriptors(self):
        outer = models.ImageDefinitionDescriptors()
        items = []

        for image_type in IMAGE_TYPES:
            for arch in IMAGE_ARCHES:
                items.append(
                    models.ImageDefinitionDescriptor(
                        name = image_type[0],
                        architecture = arch,
                        description = image_type[1],
                    )
                )

        outer.image_definition_descriptor = items
        return outer

    @exposed
    def getImageDefinitionDescriptor(self):
       raise exceptions.NotImplementedError


