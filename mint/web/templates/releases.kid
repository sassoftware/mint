<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head/>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER
    ?>

    <div py:def="breadcrumb()" class="pad">
        You are here:
        <a href="#">rpath</a>
        <a href="../">${project.getName()}</a>
        <a href="#">Releases </a>
    </div>

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
                <table border="0" cellspacing="0" cellpadding="0" class="releasestable">
                    <tr py:for="release in [x for x in releases if x.getPublished()]">

                        <th>
                            <a href="release?id=${release.getId()}">
                                ${release.getTroveName()}=${release.getTroveVersion().trailingRevision().asString()}
                            </a>
                        </th>
                        <td py:if="isOwner"><a href="#" id="{release.getId()}Edit" class="option">Edit</a></td>
                        <td py:if="isOwner"><a href="#" class="option">Delete</a></td>
                    </tr>
                </table>
                
                <div py:if="isOwner">

                    <h3>Unpublished Releases</h3>
                    <table border="0" cellspacing="0" cellpadding="0" class="releasestable">
                        <tr py:for="release in [x for x in releases if not x.getPublished()]">
                            <th>
                                <a id="release" href="release?id=${release.getId()}">
                                    ${release.getTroveName()}=${release.getTroveVersion().trailingRevision().asString()}
                                </a>
                            </th>
                            <td py:if="isOwner"><a href="#" id="{release.getId()}Edit" class="option">Edit</a></td>
                            <td py:if="isOwner"><a href="#" class="option">Delete</a></td>
                        </tr>

                    </table>
                    <p py:if="isOwner"><a href="newRelease">Create a new release</a></p>
                </div>
            </div>
        </td>
        ${projectsPane()}
    </body>
</html>
