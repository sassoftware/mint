<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker, projectText
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Images: %s' % project.getNameForDisplay())}</title>
        <link py:if="builds" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Images" href="${basePath}rss" />
    </head>

    <div py:strip="True" py:def="buildsTableRow(build, rowNumber)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            rowAttrs = { 'class': (rowNumber % 2) and 'odd' or 'even' }
            isPublished = build.getPublished()
        ?>
        <tr py:attrs="rowAttrs">
            <td colspan="3" class="buildName"><a href="${basePath}build?id=${build.id}">${truncateForDisplay(build.name)}</a>
                <span py:if="isPublished" class="buildAssociated">
                    <?python
                        release = self.client.getPublishedRelease(build.pubReleaseId)
                    ?>
                    <br />Part of ${isPublished and 'published' or 'unpublished'} release <a href="${basePath}release?id=${release.id}">${release.name} (Version ${release.version}) </a></span>
            </td>
        </tr>
        <tr py:attrs="rowAttrs">
            <td class="buildInfo">${build.getTroveName()}<br />${"%s/%s" % (build.getTroveVersion().trailingLabel(), build.getTroveVersion().trailingRevision())}</td>
            <td py:if="build.getBuildType() != buildtypes.IMAGELESS" class="buildInfo">${build.getArch()}&nbsp;${buildtypes.typeNamesShort.get(build.getBuildType(), 'Unknown')}</td>
            <td py:if="build.getBuildType() == buildtypes.IMAGELESS" class="buildInfo">&nbsp;${buildtypes.typeNamesShort.get(build.getBuildType(), 'Unknown')}</td>
            <td class="buildInfo">&nbsp;<input py:if="not isPublished" style="float: right;" name="buildIdsToDelete" type="checkbox" value="${build.id}" />
            </td>
        </tr>
    </div>

     <div py:strip="True" py:def="buildsTable(builds)">
        <div py:if="builds" py:strip="True">
            <form method="post" action="deleteBuilds">
                <table py:if="builds" border="0" cellspacing="0" cellpadding="0" class="buildstable">
                    <div py:strip="True" py:for="rowNumber, build in enumerate(builds)">
                        ${buildsTableRow(build, rowNumber)}
                    </div>
                </table>
                <p><button id="deleteBuildsSubmit" type="submit">Delete Selected Images</button></p>
            </form>
        </div>
        <p py:if="not builds">This ${projectText().lower()} contains no images.</p>
    </div>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(projectPublishedReleases, isOwner)}
                ${commitsMenu(projectCommits)}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>

                <h2>Images</h2>
                <p py:if="isWriter">You may <a href="newBuild">create a new image</a> or <a href="newBuildsFromProductDefinition">create a set of images from a product definition</a>.</p>
                ${buildsTable(builds)}
            </div>
        </div>
    </body>

</html>
