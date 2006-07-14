<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.helperfuncs import truncateForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <?python
        isOwner = (userLevel == userlevels.OWNER or auth.admin)
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()

        # FIXME: releases, not builds
        #builds = project.getBuilds()
        commits = project.getCommits()
    ?>
    <head>
        <title>${formatTitle("Project Page: %s"%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                <!-- FIXME: releases, not builds
                ${buildsMenu(builds, isOwner)} -->
                ${commitsMenu(commits)}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 25)}</h1>
                <h2 py:if="project.getProjectUrl()">Project Help</h2>

                <h3>Help Topics</h3>
                <ul>
                    <li py:if="isOwner or isDeveloper">
                        <a href="${basePath}conaryDevelCfg">Setting up ${isOwner and "your" or "the"} project build environment</a>
                    </li>
                    <li><a href="${basePath}conaryUserCfg">Installing packages from ${isOwner and "your" or "this"} project</a></li>
                </ul>
            </div>
        </div>
    </body>
</html>
