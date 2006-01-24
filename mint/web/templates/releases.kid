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

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="#">Releases</a>
    </div>

    <tr py:def="releaseTableRow(releaseName, release, isOwner, isFirst, numReleasesInVersion)">
        <?python files = release.getFiles() ?>
        <td py:if="isFirst" rowspan="${numReleasesInVersion}">
            ${release.getName()}<br />
            <span style="color: #999">${releaseName}</span>
        </td>
        <td>
                <a href="release?id=${release.getId()}">${release.getArch()}</a>
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
        <td><a href="publish?releaseId=${release.getId()}" id="${release.getId()}Publish" class="option">Publish</a>
        </td>
        </div>
    </tr>


     <div py:strip="True" py:def="releasesTable(releases, releaseVersions, isOwner, wantPublished)">
        <?python filteredReleases = [x for x in releases if x.getPublished() == wantPublished]?>
        <table border="0" cellspacing="0" cellpadding="0" class="releasestable">            <tr py:if="filteredReleases">
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
            ?>
            <div py:strip="True" py:if="filteredReleasesForVersion" rowspan="${len(filteredReleasesForVersion)}">
                <div py:strip="True" py:for="release in filteredReleasesForVersion">
                    ${releaseTableRow(releaseName, release, isOwner, (lastReleaseName != releaseName), len(filteredReleasesForVersion))}
                    <?python lastReleaseName = releaseName ?>
                </div>
            </div>
        </div>
        </table>
        <p py:if="not filteredReleases">This project
            has no ${wantPublished and "published" or "unpublished"}
            releases.</p>
        <p py:if="isOwner and wantPublished"><strong><a href="newRelease">Create a new release</a></strong></p>
    </div>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                ${releasesMenu(publishedReleases, isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getNameForDisplay(maxWordLen = 50)}<br />Releases</h2>
                <h3 py:if="isOwner">Published Releases</h3>
                ${releasesTable(releases, releaseVersions, isOwner, True)}
            </div>
            <div class="pad">
                <div py:if="isOwner">
                    <h3>Unpublished Releases</h3>
                    ${releasesTable(releases, releaseVersions, isOwner, False)}
                </div>
            </div>

        </td>
        <td id="right" class="projects">
            <div class="pad">
                ${groupTroveBuilder()}
            </div>
        </td>
    </body>
</html>
