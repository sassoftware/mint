<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Group Builder: %s' % project.getName())}</title>
    </head>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Group Builder</a>
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
                <h1>Group Builder</h1>

                <p>You can create a group here. The group defines what your application image contains.</p>

                <h2>Currently In Progress</h2>
                
                <ul>
                    <li py:if="groupTrove and groupTrove.projectId == project.id" style="font-weight: bold;">
                        <a href="${basePath}editGroup?id=${groupTrove.id}">${groupTrove.recipeName}</a> (${len(groupTrove.listTroves())} troves)
                    </li>
                    <li py:if="not groupTrove">
                        You are not currently working on a group.
                    </li>
                </ul>

                <h2>Other Groups</h2>

                <p>Click on a group name to stop working on the current group and begin editing another.</p>
                <ul>
                    <li py:for="gt in groupTrovesInProject">
                        <a href="${basePath}editGroup?id=${gt[0]}">${gt[1]} <span py:if="groupTrove and groupTrove.id == gt[0]">(currently selected)</span></a> <a href="${basePath}deleteGroup?id=${gt[0]}">Delete</a>
                    </li>
                    <li>
                        <a href="${basePath}newGroup"><b>Create a new group.</b></a>
                    </li>
                </ul>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
            <td class="pad">
                ${groupTroveBuilder()}
            </td>
        </td>
    </body>
</html>
