<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Builds: %s' % project.getNameForDisplay())}</title>
        <link py:if="builds" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Builds" href="${basePath}rss" />
    </head>

    <div py:strip="True" py:def="buildsTableRow(build, rowNumber, numShowByDefault, hiddenName)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            rowAttrs = (rowNumber >= numShowByDefault) and { 'name': hiddenName, 'style': 'display: none;' } or {}
            rowAttrs['class'] = (rowNumber % 2) and 'odd' or 'even'
            isPublished = build.getPublished()
            isInProgress = build.id in buildsInProgress
        ?>
        <tr py:attrs="rowAttrs">
            <td colspan="4" class="buildName"><a href="${basePath}build?id=${build.id}">${truncateForDisplay(build.name)}</a>
                <span py:if="build.pubReleaseId" class="buildAssociated">
                    <?python
                        release = self.client.getPublishedRelease(build.pubReleaseId)
                    ?>
                    <br />Part of ${isPublished and 'published' or 'unpublished'} release <a href="${basePath}release?id=${release.id}">${release.name} (Version ${release.version}) </a></span>
                <div py:if="build.id in buildsInProgress" py:strip="True">
                    <br /><span class="buildAssociated">This build is currently in progress.</span>
                </div>
            </td>
        </tr>
        <tr py:attrs="rowAttrs">
            <td class="buildInfo">${build.getDefaultName()}</td>
            <td class="buildInfo">${build.getArch()}</td>
            <td class="buildInfo">${buildtypes.typeNamesShort[build.getBuildType()]}</td>
            <td class="buildInfo">&nbsp;<input py:if="not isPublished and not isInProgress" style="float: right;" name="buildIdsToDelete" type="checkbox" value="${build.id}" />
            </td>
        </tr>
    </div>

     <div py:strip="True" py:def="buildsTable(builds, numShowByDefault)">
        <?python
            rowNumber = 0
            hiddenName = 'older_build'
        ?>
        <div py:if="builds" py:strip="True">
            <form method="post" action="deleteBuilds">
                <table py:if="builds" border="0" cellspacing="0" cellpadding="0" class="buildstable">
                    <div py:strip="True" py:for="build in builds">
                        ${buildsTableRow(build, rowNumber, numShowByDefault, hiddenName)}
                        <?python rowNumber += 1 ?>
                    </div>
                </table>
        <p py:if="rowNumber > numShowByDefault"><a name="${hiddenName}" onclick="javascript:toggle_display_by_name('${hiddenName}');" href="#">(show all builds)</a></p>
                <p><button id="deleteBuildsSubmit" type="submit">Delete Selected Builds</button></p>
            </form>
        </div>
        <p py:if="not builds">This project contains no builds.</p>
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
                <h2>Builds</h2>
                <p py:if="isWriter"><strong><a href="newBuild">Create a new build</a></strong></p>
                ${buildsTable(builds, 10)}
            </div>
        </div>
    </body>

</html>
