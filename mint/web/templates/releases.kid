<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head/>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER
        releases = project.getReleases()
    ?>
    <body>
        <h2>Project Releases</h2>       

        <ul>
            <li py:for="release in releases">
                <a href="release?id=${release.getId()}">${release.getTroveName()}=${release.getTroveVersion().trailingRevision().asString()}</a>
            </li>
        </ul>
        <p py:if="isOwner"><a href="newRelease">Create a new release</a></p>
    </body>
</html>
