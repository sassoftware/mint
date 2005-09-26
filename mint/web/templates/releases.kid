<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Releases: %s' % project.getName())}</title>
    </head>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER or auth.admin
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Releases</a>
    </div>

    <table border="0" cellspacing="0" cellpadding="0"
           class="releasestable" py:def="releasesTable(releaseList, isOwner)">
        <tr py:for="release in releaseList">

            <th>
                <a href="release?id=${release.getId()}">
                    ${release.getTroveName()}=${release.getTroveVersion().trailingRevision().asString()}
                </a>
            </th>
            <td py:if="isOwner"><a href="editRelease?releaseId=${release.getId()}"
                                   id="{release.getId()}Edit" class="option">Edit</a>
            </td>
        </tr>
    </table>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />releases</h2>
                <h3 py:if="isOwner">Published Releases</h3>
                ${releasesTable([x for x in releases if x.getPublished()], isOwner)}
                <p py:if="not releases">This project has no releases.</p>

                <div py:if="isOwner">

                    <h3>Unpublished Releases</h3>
                    ${releasesTable([x for x in releases if not x.getPublished()], isOwner)}
                    <p py:if="isOwner"><a href="newRelease">Create a new release</a></p>
                </div>
            </div>
        </td>
        ${projectsPane()}
    </body>
</html>
