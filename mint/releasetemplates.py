# Copyright (c) 2004-2006 rPath, Inc.
#
# All Rights Reserved
#
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM
from mint import releasetypes

# *** Extremely Important ***
# Changing the names or semantic meanings of the keys to data templates is the
# same thing as making a schema upgrade! do not do this lightly.

imageGenTemplate = {
    # XXX this is kind of a lousy description; a toggleable "override ILP option would be nicer
    'installLabelPath': (RDT_STRING, '',  'Custom Conary installLabelPath setting (leave blank for default)'),
    'autoResolve':      (RDT_BOOL, False, 'Automatically install required dependencies during updates'),
    }

installableIsoTemplate = imageGenTemplate.copy()
installableIsoTemplate.update({
    'showMediaCheck':   (RDT_BOOL, False, 'Prompt to verify CD/DVD images during install'),
    'betaNag':          (RDT_BOOL, False, 'This release is considered a beta'),
    'bugsUrl':          (RDT_STRING, 'http://bugs.rpath.com/', 'Bug report URL'),
    'maxIsoSize':       (RDT_ENUM, '681574400', 'ISO Size',
                         releasetypes.discSizes)
    })

bootableImageTemplate = imageGenTemplate.copy()
bootableImageTemplate.update({
    'freespace':        (RDT_INT, 250, 'How many megabytes of free space should be allocated in the image?'),
    })

rawHdTemplate = bootableImageTemplate.copy()
rawFsTemplate = bootableImageTemplate.copy()

vmwareImageTemplate = bootableImageTemplate.copy()
vmwareImageTemplate.update({
    'vmMemory':         (RDT_INT, 256, 'How much memory should VMware use when running this image?')
    })

liveIsoTemplate = imageGenTemplate.copy()
liveIsoTemplate.update({
    'unionfs':          (RDT_BOOL, True, 'Use unionfs (recommended)'),
    'zisofs' :          (RDT_BOOL, True, 'Compress filesystem')
    })

tarballTemplate = imageGenTemplate.copy()

stubImageTemplate = {
    'boolArg'   : (RDT_BOOL, False, 'Garbage Boolean'),
    'stringArg' : (RDT_STRING, '', 'Garbage String'),
    'intArg'    : (RDT_INT, 0, 'Garbage Integer'),
    'enumArg'   : (RDT_ENUM, '2', 'Garbage Enum',
                   {'foo' : '0', 'bar': '1', 'baz': '2'})
    }

dataHeadings = {
    releasetypes.INSTALLABLE_ISO  : 'Installable CD/DVD Settings',
    releasetypes.RAW_HD_IMAGE     : 'Raw Hard Disk Settings',
    releasetypes.RAW_FS_IMAGE     : 'Raw Filesystem Settings',
    releasetypes.TARBALL          : 'Tarball Settings',
    releasetypes.VMWARE_IMAGE     : 'VMware Image Settings',
    releasetypes.LIVE_ISO         : 'Live CD/DVD Settings',
    releasetypes.STUB_IMAGE       : 'Stub Image Settings',
    }

dataTemplates = {
    releasetypes.INSTALLABLE_ISO  : installableIsoTemplate,
    releasetypes.RAW_HD_IMAGE     : rawHdTemplate,
    releasetypes.RAW_FS_IMAGE     : rawFsTemplate,
    releasetypes.VMWARE_IMAGE     : vmwareImageTemplate,
    releasetypes.LIVE_ISO         : liveIsoTemplate,
    releasetypes.TARBALL          : tarballTemplate,
    releasetypes.STUB_IMAGE       : stubImageTemplate,
    }
