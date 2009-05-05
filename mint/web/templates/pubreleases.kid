<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker, projectText
from mint import buildtypes
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Published Releases: %s' % project.getNameForDisplay())}</title>
        <link py:if="projectReleases" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />
    </head>

    <div py:def="pubReleasesTable(releases, isOwner)">
        <table class="releasestable" border="0" cellspacing="0" cellpadding="0" >
            <?python rowNumber = 0?>
            <div py:for="release in releases" py:strip="True">
                <?python
                    uniqueBuildTypeNames = []
                    for buildType, arch, extraFlags in release.getUniqueBuildTypes():
                        if buildType == buildtypes.IMAGELESS:
                            arch = ''
                        x = "%s %s" % (arch, buildtypes.typeNamesMarketing[buildType])
                        if extraFlags:
                            x += " (%s)" % (", ".join(extraFlags))
                        uniqueBuildTypeNames.append(x)
                ?>
                <tr py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td class="releaseName" colspan="2"><a href="${basePath}release?id=${release.id}">${release.name}</a></td>
                </tr>
                <tr py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td class="releaseInfo">Version ${release.version}</td>
                    <td class="releaseInfoRight">
                        <div py:if="uniqueBuildTypeNames">
                            <span py:for="buildTypeName in uniqueBuildTypeNames">${buildTypeName}<br /></span>
                        </div>
                        <div py:if="not uniqueBuildTypeNames">
                            This release is empty.
                        </div>
                    </td>
                </tr>
                <tr py:if="release.description" py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td colspan="2" class="releaseInfo" py:content="release.description" />
                </tr>
                <tr py:if="isOwner" py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td colspan="2" class="releaseInfo">
                        <span py:if="not release.isPublished()">(<a href="${basePath}editRelease?id=${release.id}">edit</a>)&nbsp;<span py:if="uniqueBuildTypeNames">(<a href="${basePath}publishRelease?id=${release.id}">publish</a>)&nbsp;</span>(<a href="${basePath}deleteRelease?id=${release.id}">delete</a>)</span>
                        <span py:if="release.isPublished()">(<a href="${basePath}unpublishRelease?id=${release.id}">unpublish</a>)</span></td>
                </tr>
                <?python rowNumber += 1 ?>
            </div>
        </table>
    </div>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
                <div id="right" class="side">
                    ${resourcePane()}
                </div>
                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Releases</div>
                    <p py:if="isOwner">
                        <a class="pageSectionLink" href="newRelease">Create a new release</a>
                    </p>
                    <div py:if="not projectReleases">
                        This ${projectText().lower()} currently has no releases.
                    </div>
                    <div py:if="projectPublishedReleases">
                        ${pubReleasesTable(projectPublishedReleases, isOwner)}
                    </div>
                    <div py:if="projectUnpublishedReleases and isWriter">
                        <h3>Unpublished Releases</h3>
                        ${pubReleasesTable(projectUnpublishedReleases, isOwner)}
                    </div>
    
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>   
        </div>
    </body>
</html>
