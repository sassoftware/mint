<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
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

    <div py:strip="True" py:def="buildsTableRow(build, isHidden, hiddenName)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            rowAttrs = isHidden and { 'name': hiddenName, 'style': 'display: none;' } or {}
        ?>
        <tr py:attrs="rowAttrs">
            <td><a href="${basePath}build?id=${build.id}">${truncateForDisplay(build.name)}</a><br />
                <span class="smallSpecs" colspan="2">
                    ${build.getArch()}&nbsp;${buildtypes.typeNamesShort[build.getBuildType()]}&nbsp;&nbsp;&nbsp;${build.getDefaultName()}
                </span>
            </td>
        </tr>
    </div>

     <div py:strip="True" py:def="buildsTable(builds, numShowByDefault)">
        <?python
            ithBuild = 0
            hiddenName = 'older_build'
        ?>
        <table py:if="builds" border="0" cellspacing="0" cellpadding="0" class="buildstable">
            <div py:strip="True" py:for="build in builds">
                ${buildsTableRow(build, ithBuild > numShowByDefault, hiddenName)}
                <?python ithBuild += 1 ?>
            </div>
        </table>
        <p py:if="ithBuild > numShowByDefault"><a name="${hiddenName}" onclick="javascript:toggle_display_by_name('${hiddenName}');" href="#">(show all builds)</a></p>
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
