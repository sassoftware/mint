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
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER or auth.admin
        isWriter = (userLevel in userlevels.WRITERS) or auth.admin
    ?>
    <div py:strip="True" py:def="buildTableRow(buildName, build, isOwner, isWriter, isFirst, numBuildsInVersion, defaultHidden, hiddenName)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            files = build.getFiles()
            rowAttrs = defaultHidden and { 'name': hiddenName, 'style': 'display: none;' } or {}
        ?>
        <tr py:attrs="rowAttrs">
            <td py:if="isFirst" rowspan="${numBuildsInVersion}">
                ${truncateForDisplay(build.getName(), maxWordLen=25)}<br />
                <span style="color: #999">${truncateForDisplay(buildName, maxWordLen=30)}</span>
            </td>
            <td>
                    <a href="build?id=${build.getId()}">${build.getArch()} ${buildtypes.typeNamesShort[build.buildType]}</a>
            </td>
            <td py:if="build.getPublished()">
                <div py:strip="True" py:for="i, file in enumerate(files)">
                    <?py fileUrl = cfg.basePath + "downloadImage/" + str(file['fileId']) + "/" + file['filename'] ?>
                    <a py:attrs="downloadTracker(cfg, fileUrl)" href="http://${cfg.siteHost}${fileUrl}">
                        ${file['title'] and file['title'] or "Disc " + str(i+1)}
                    </a> (${file['size']/1048576}&nbsp;MB)<br />
                </div>
                <span py:if="not files">N/A</span>
            </td>
            <td py:if="isWriter and not build.getPublished()"><a onclick="javascript:deleteBuild(${build.getId()});" href="#" class="option">Delete</a> 
            </td>
        </tr>
    </div>

     <div py:strip="True" py:def="buildsTable(builds, buildVersions, isOwner, isWriter, wantPublished, numShowByDefault)">
        <?python
            ithBuild = 0
            filteredBuilds = [x for x in builds if x.getPublished() == wantPublished]
            hiddenName = 'older_build_' + (wantPublished and 'p' or 'u')
        ?>
        <table border="0" cellspacing="0" cellpadding="0" class="buildstable">
            <tr py:if="filteredBuilds">
                <th>Name</th>
                <th>Built For</th>
                <th colspan="2" py:if="isOwner and not wantPublished">&nbsp;</th>
                <div py:strip="True" py:if="wantPublished">
                    <th>Downloads</th>
                </div>
            </tr>
        <div py:strip="True" py:for="buildName, buildsForVersion in buildVersions">
            <?python
                filteredBuildsForVersion = [ x for x in buildsForVersion if x.getPublished() == wantPublished ]
                isFirst = True
                lastBuildName = ""
                hideByDefault = (ithBuild >= numShowByDefault)
            ?>
            <div py:strip="True" py:if="filteredBuildsForVersion" rowspan="${len(filteredBuildsForVersion)}">
                <div py:strip="True" py:for="build in filteredBuildsForVersion">
                    ${buildTableRow(buildName, build, isOwner, isWriter, (lastBuildName != buildName), len(filteredBuildsForVersion), hideByDefault, hiddenName)}
                    <?python lastBuildName = buildName ?>
                </div>
            </div>
            <?python
                if filteredBuildsForVersion:
                    ithBuild += 1
            ?>
        </div>
        </table>
        <p py:if="not filteredBuilds">This project has no ${wantPublished and "published" or "unpublished"} builds.</p>
        <p py:if="ithBuild > numShowByDefault"><a name="${hiddenName}" onclick="javascript:toggle_display_by_name('${hiddenName}');" href="#">(show all ${wantPublished and "published" or "unpublished"} builds)</a></p>
        <p py:if="isWriter and wantPublished"><strong><a href="newBuild">Create a new build</a></strong></p>
    </div>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                <!-- FIXME - releases, not builds
                ${buildsMenu(publishedBuilds, isOwner)} -->
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <?python hasVMwareImage = True in [ x.hasVMwareImage() for x in publishedBuilds ] ?>
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2><a py:if="hasVMwareImage" title="Download VMware Player" href="http://www.vmware.com/download/player/"><img class="vmwarebutton" src="${cfg.staticPath}apps/mint/images/get_vmware_player.gif" alt="Download VMware Player" /></a>Builds</h2>
                <h3 py:if="isWriter">Published Builds</h3>
                ${buildsTable(builds, buildVersions, isOwner, isWriter, True, 5)}

                <div py:if="isWriter">
                    <h3>Unpublished Builds</h3>
                    ${buildsTable(builds, buildVersions, isOwner, isWriter, False, 5)}
                </div>
            </div>
        </div>
    </body>
</html>
