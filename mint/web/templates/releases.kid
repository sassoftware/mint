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
        <td py:if="isFirst" rowspan="${numReleasesInVersion}">
                ${releaseName}
        </td>
        <td class="relname">
                <a href="release?id=${release.getId()}">${release.getArch()}</a>
        </td>
        <div py:strip="True" py:if="isOwner and not release.getPublished()">
        <td><a href="editRelease?releaseId=${release.getId()}" id="${release.getId()}Edit" class="option">Edit</a>
        </td>
        <td><a href="deleteRelease?releaseId=${release.getId()}" id="${release.getId()}Delete" class="option">Delete</a>
        </td>
        <td><a href="publish?releaseId=${release.getId()}" id="${release.getId()}Publish" class="option">Publish</a>
        </td>
        </div>
    </tr>

    <div py:strip="True" py:def="releasesTable(releaseVersions, isOwner, wantPublished)">
        <table border="0" cellspacing="0" cellpadding="0" class="releasestable">
        <div py:strip="True" py:for="releaseName, releasesForVersion in releaseVersions.items()">
            <?python
                filteredReleasesForVersion = [ x for x in releasesForVersion if x.getPublished() == wantPublished ]
                isFirst = True
                lastReleaseName = ""
            ?>
            <div py:strip="True" py:if="filteredReleasesForVersion" rowspan="${len(filteredReleasesForVersion)}">
                <tr>
                    <th>Name</th>
                    <th>Architecture</th>
                    <th colspan="3" py:if="isOwner and not wantPublished">Options</th>
                </tr>
                <div py:strip="True" py:for="release in filteredReleasesForVersion">
                    ${releaseTableRow(releaseName, release, isOwner, (lastReleaseName != releaseName), len(filteredReleasesForVersion))}
                    <?python lastReleaseName = releaseName ?>
                </div>
            </div>
        </div>
        </table>
        <p py:if="not filteredReleasesForVersion">This project
            has no ${wantPublished and "published" or "unpublished"}
            releases.</p>
        <p py:if="isOwner and wantPublished"><strong><a href="newRelease">Create a new release</a></strong></p>
    </div>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                ${releasesMenu(publishedReleases, isOwner, display="none")}
                ${commitsMenu(project.getCommits(), display="none")}
                ${browseMenu(display='none')}
                ${searchMenu(display='none')}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getNameForDisplay(maxWordLen = 50)}<br />Releases</h2>
                <h3 py:if="isOwner">Published Releases</h3>
                ${releasesTable(releaseVersions, isOwner, True)}
            </div>
            <div class="pad">
                <div py:if="isOwner">
                    <h3>Unpublished Releases</h3>
                    ${releasesTable(releaseVersions, isOwner, False)}
                </div>
            </div>

        </td>
        <td id="right" class="projects">
            ${projectsPane()}
            <div class="pad">
                ${groupTroveBuilder()}
            </div>
        </td>
    </body>
</html>
