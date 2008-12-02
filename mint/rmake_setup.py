#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import os

from mint import database
from mint import helperfuncs
from mint import shimclient

from conary.lib import util

def setupRmake(cfg, rmakeConfigFilePath):
    # Create a product (as the admin user) for use by the internal rmake.
    adminClient = shimclient.ShimMintClient(cfg,
        [cfg.authUser, cfg.authPass])

    shortName = 'rmake-repository'

    # ensure the rMake repository doesn't exist by attempting to reference it
    try:
        adminClient.getProjectByHostname('rmake-repository')
    except database.ItemNotFound:
        pass
    else:
        raise RuntimeError('rMake repository already configured')

    projectId = adminClient.newProject(name="rMake Repository",
        hostname=shortName,
        domainname=str(cfg.projectDomainName),
        projecturl="",
        desc="Please consider the contents of this product's repository to be for REFERENCE PURPOSES ONLY.\nThis product's repository is used by the rMake server running on this rBuilder for building packages and groups with Package Creator and Appliance Creator. This product is for the internal use of the rBuilder server. Do not attempt to manipulate the contents of this repository. Do not shadow, clone or otherwise reference any packages or components from this repository. This product can be reset at any time, which would lead to errors in anything that references the contents of this product's repository.",
        appliance="no",
        shortname=shortName,
        namespace="rpath",
        prodtype="Component",
        version="1",
        commitEmail="",
        isPrivate=True,
        projectLabel="")

    rmakeUser = "%s-user" % shortName
    rmakePassword = helperfuncs.genPassword(32)
    adminClient.addProjectRepositoryUser(projectId, rmakeUser,
        rmakePassword)

    _writeRmakeConfig(rmakeConfigFilePath, rmakeUser, rmakePassword,
        "https://%s" % cfg.siteHost,
        "%s.%s" % (shortName, cfg.projectDomainName),
        "https://%s/repos/%s" % (cfg.siteHost, shortName))

    if os.environ.get('RBUILDER_NOSUDO', False):
        sudo = ''
    else:
        sudo = 'sudo '

    os.system("%s/sbin/service rmake restart" % sudo)
    os.system("%s/sbin/service rmake-node restart" % sudo)

def _writeRmakeConfig(path, user, password, rBuilderUrl, reposName, reposUrl):
    util.mkdirChain(os.path.dirname(path))
    f = file(path, 'w')
    f.write('%s %s %s %s\n' % ('reposUser', reposName, user, password))
    f.write('%s %s\n' % ('reposName', reposName))
    f.write('%s %s\n' % ('reposUrl', reposUrl))
    f.write('%s %s\n' % ('rBuilderUrl', rBuilderUrl))
    f.close()

