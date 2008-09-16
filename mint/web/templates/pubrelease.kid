<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
# All Rights Reserved
#
from mint.helperfuncs import formatTime
from mint.helperfuncs import truncateForDisplay
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
            
            <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>
                
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen=30)}</h1>
                <div class="page-title">Release: ${release.name}, version ${release.version}</div>

                <p py:if="isWriter">
                    <span py:strip="True" py:if="release.isPublished()">This release has been published and can be viewed by the public. <span py:strip="True" py:if="isOwner">(<a href="unpublishRelease?id=${release.id}">Unpublish this release.</a>)</span></span>
                    <span py:strip="True" py:if="not release.isPublished()">This release has not been published yet. <span py:strip="True" py:if="isOwner">(<a href="publishRelease?id=${release.id}">Publish this release.</a>)</span></span>
                </p>

                <div class="help" py:if="release.timeCreated">Release created ${formatTime(release.timeCreated)}</div>
                <div class="help" py:if="release.timeCreated != release.timeUpdated and release.timeUpdated">Release updated ${formatTime(release.timeUpdated)}</div>
                <div class="help" py:if="release.isPublished() and release.timePublished">Release published ${formatTime(release.timePublished)}</div>

                <h2>Description</h2>
                <p py:if="not release.description">Release has no description.</p>
                <p py:for="line in release.description.splitlines()">
                    ${truncateForDisplay(line, 100000000, 70)}
                </p>
                    <div id="builds">
                        <h2>Images</h2>
                        ${buildTable(builds)}
                        <p py:if="not builds">Release contains no images.</p>
                    </div>
                </div><br class="clear" />
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>   
        </div>
    </body>
</html>
