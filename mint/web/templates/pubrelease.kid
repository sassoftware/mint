<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Release: %s' % project.getNameForDisplay())}</title>
    </head>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import buildtypes
        hasVMwareBuild = bool(buildtypes.VMWARE_IMAGE in [x.getBuildType() for x in builds])
    ?>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen=30)}</h1>
                <h2>Release: ${release.name}, version ${release.version}</h2>

                <p py:if="isWriter">
                    <span py:strip="True" py:if="release.isPublished()">This release has been published and can be viewed by the public. <span py:strip="True" py:if="isOwner">(<a href="unpublishRelease?id=${release.id}">Unpublish this release.</a>)</span></span>
                    <span py:strip="True" py:if="not release.isPublished()">This release has not been published yet. <span py:strip="True" py:if="isOwner">(<a href="publishRelease?id=${release.id}">Publish this release.</a>)</span></span>
                </p>

                <h3>Description</h3>
                <p>${release.description.strip() or "Release has no description."}</p>
                <div id="builds">
                    <h3><a py:if="hasVMwareBuild" title="Download VMware Player" href="http://www.vmware.com/download/player/"><img class="vmwarebutton" src="${cfg.staticPath}apps/mint/images/get_vmware_player.gif" alt="Download VMware Player" /></a>Builds</h3>
                    ${buildTable(builds)}
                    <p py:if="not builds">Release contains no builds.</p>
                </div>
            </div>
        </div>
    </body>
</html>
