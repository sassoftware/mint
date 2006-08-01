<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker
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
                    uniqueBuildTypes = release.getUniqueBuildTypes()
                    uniqueBuildTypeNames = [ "%s %s" % (x[1], buildtypes.typeNamesMarketing[x[0]]) for x in uniqueBuildTypes ]
                ?>
                <tr py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td class="releaseName" colspan="2"><a href="${basePath}release?id=${release.id}">${release.name}</a></td>
                </tr>
                <tr py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td class="releaseInfo">Version ${release.version}</td>
                    <td class="releaseInfoRight">
                        <div py:if="uniqueBuildTypes">
                            <span py:for="buildTypeName in uniqueBuildTypeNames">${buildTypeName}<br /></span>
                        </div>
                        <div py:if="not uniqueBuildTypes">
                            This release is empty.
                        </div>
                    </td>
                </tr>
                <tr py:if="release.description" py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td colspan="2" class="releaseInfo" py:content="release.description" />
                </tr>
                <tr py:if="isOwner" py:attrs="{'class': (rowNumber % 2) and 'odd' or 'even'}">
                    <td colspan="2" class="releaseInfo">
                        <span py:if="not release.isPublished()">(<a href="${basePath}editRelease?id=${release.id}">edit</a>)&nbsp;<span py:if="uniqueBuildTypes">(<a href="${basePath}publishRelease?id=${release.id}">publish</a>)&nbsp;</span>(<a href="${basePath}deleteRelease?id=${release.id}">delete</a>)</span>
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
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2>Releases</h2>
                <p py:if="isOwner">
                    <strong><a href="newRelease">Create a new release</a></strong>
                </p>
                <div py:if="not projectReleases">
                    This project currently has no releases.
                </div>
                <div py:if="projectPublishedReleases">
                    ${pubReleasesTable(projectPublishedReleases, isOwner)}
                </div>
                <div py:if="projectUnpublishedReleases and isOwner">
                    <h3>Unpublished Releases</h3>
                    ${pubReleasesTable(projectUnpublishedReleases, isOwner)}
                </div>

            </div>
        </div>
    </body>
</html>
