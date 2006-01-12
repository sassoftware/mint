<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
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

    <table border="0" cellspacing="0" cellpadding="0"
           class="releasestable" py:def="releasesTable(releaseList, isOwner)">
        <tr py:for="release in releaseList">

            <th>
                <a href="release?id=${release.getId()}">
                    ${release.getTroveName()}=${release.getTroveVersion().trailingRevision().asString()} (${release.getArch()})
                </a>
            </th>
            <td py:if="isOwner and not release.getPublished()"><a href="editRelease?releaseId=${release.getId()}"
                                   id="{release.getId()}Edit" class="option">Edit</a>
            </td>
            <td py:if="isOwner and not release.getPublished()"><a href="deleteRelease?releaseId=${release.getId()}"
                                   id="{release.getId()}Delete" class="option">Delete</a>
            </td>
        </tr>
    </table>

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
                ${releasesTable(publishedReleases, isOwner)}
                <p py:if="not publishedReleases">This project has no published releases.</p>

                <?python unpublishedReleases = list(set(releases) - set(publishedReleases)) ?>
                <div py:if="isOwner and unpublishedReleases">
                    <h3>Unpublished Releases</h3>
                    ${releasesTable(unpublishedReleases, isOwner)}
                </div>

                <p py:if="isOwner"><a href="newRelease">Create a new release</a></p>
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
