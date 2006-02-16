<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Releases: %s' % project.getNameForDisplay())}</title>
        <link py:if="releases" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />
    </head>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER or auth.admin
    ?>
    <div py:strip="True" py:def="releaseTableRow(releaseName, release, isOwner, isFirst, numReleasesInVersion, defaultHidden, hiddenName)">
        <?python
            from mint import releasetypes
            from mint.helperfuncs import truncateForDisplay
            files = release.getFiles()
            rowAttrs = defaultHidden and { 'name': hiddenName, 'style': 'display: none;' } or {}
        ?>
        <tr py:attrs="rowAttrs">
            <td py:if="isFirst" rowspan="${numReleasesInVersion}">
                ${truncateForDisplay(release.getName(), maxWordLen=25)}<br />
                <span style="color: #999">${truncateForDisplay(releaseName, maxWordLen=30)}</span>
            </td>
            <td>
                    <a href="release?id=${release.getId()}">${release.getArch()} ${releasetypes.typeNamesShort[release.imageTypes[0]]}</a>
            </td>
            <td py:if="release.getPublished()">
                <div py:strip="True" py:for="i, file in enumerate(files)">
                    <a href="${cfg.basePath}downloadImage/${file['fileId']}/${file['filename']}">${file['title'] and file['title'] or "Disc " + str(i+1)}</a> (${file['size']/1048576}&nbsp;MB)<br />
                </div>
                <span py:if="not files">N/A</span>
            </td>
            <div py:strip="True" py:if="isOwner and not release.getPublished()">
            <td><a href="deleteRelease?releaseId=${release.getId()}" id="${release.getId()}Delete" class="option">Delete</a>
            </td>
            <td><a py:if="release.getFiles()" href="publish?releaseId=${release.getId()}" id="${release.getId()}Publish" class="option">Publish</a>
            </td>
            </div>
        </tr>
    </div>

     <div py:strip="True" py:def="releasesTable(releases, releaseVersions, isOwner, wantPublished, numShowByDefault)">
        <?python
            ithRelease = 0
            filteredReleases = [x for x in releases if x.getPublished() == wantPublished]
            hiddenName = 'older_release_' + (wantPublished and 'p' or 'u')
        ?>
        <table border="0" cellspacing="0" cellpadding="0" class="releasestable">
            <tr py:if="filteredReleases">
                <th>Name</th>
                <th>Built For</th>
                <th colspan="2" py:if="isOwner and not wantPublished">&nbsp;</th>
                <div py:strip="True" py:if="wantPublished">
                    <th>Downloads</th>
                </div>
            </tr>
        <div py:strip="True" py:for="releaseName, releasesForVersion in releaseVersions">
            <?python
                filteredReleasesForVersion = [ x for x in releasesForVersion if x.getPublished() == wantPublished ]
                isFirst = True
                lastReleaseName = ""
                hideByDefault = (ithRelease >= numShowByDefault)
            ?>
            <div py:strip="True" py:if="filteredReleasesForVersion" rowspan="${len(filteredReleasesForVersion)}">
                <div py:strip="True" py:for="release in filteredReleasesForVersion">
                    ${releaseTableRow(releaseName, release, isOwner, (lastReleaseName != releaseName), len(filteredReleasesForVersion), hideByDefault, hiddenName)}
                    <?python lastReleaseName = releaseName ?>
                </div>
            </div>
            <?python
                if filteredReleasesForVersion:
                    ithRelease += 1
            ?>
        </div>
        </table>
        <p py:if="not filteredReleases">This project has no ${wantPublished and "published" or "unpublished"} releases.</p>
        <p py:if="ithRelease > numShowByDefault"><a name="${hiddenName}" onclick="javascript:toggle_display_by_name('${hiddenName}');" href="#">(show all ${wantPublished and "published" or "unpublished"} releases)</a></p>
        <p py:if="isOwner and wantPublished"><strong><a href="newRelease">Create a new release</a></strong></p>
    </div>

    <body>
        <div class="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(publishedReleases, isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${groupTroveBuilder()}
            </div>
            <div id="middle">
                <?python hasVMwareImage = True in [ x.hasVMwareImage() for x in publishedReleases ] ?>
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2><a py:if="hasVMwareImage" title="Download VMware Player" href="http://www.vmware.com/download/player/"><img class="vmwarebutton" src="${cfg.staticPath}apps/mint/images/get_vmware_player.gif" alt="Download VMware Player" /></a>Releases</h2>
                <h3 py:if="isOwner">Published Releases</h3>
                ${releasesTable(releases, releaseVersions, isOwner, True, 5)}

                <div py:if="isOwner">
                    <h3>Unpublished Releases</h3>
                    ${releasesTable(releases, releaseVersions, isOwner, False, 5)}
                </div>
            </div>
        </div>
    </body>
</html>
