<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Group Builder: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(projectPublishedReleases, isOwner)}
                ${commitsMenu(projectCommits)}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

            <div id="middle">
                <h1>Group Builder</h1>

                <p>You can use Group Builder to create a group that
                describes the packages you want your distribution to
                contain.</p>

                <p>Once Group Builder creates your group, you can browse or
                search any ${cfg.productName} project for packages, and add
                them to the current group.  When you are done adding
                packages, you can cook the group, which commits it into
                your project's repository.  At that point, you can create a
                build based on the group.</p>

                <h2>Current Group</h2>

                <ul>
                    <li py:if="not groupTrove">
                        You are not currently building a group.
                    </li>

                    <li py:if="groupTrove">
                        The following group is currently being built:
                    </li>

                    <li py:if="groupTrove and groupTrove.projectId == project.id" style="font-weight: bold;">
                        <a href="${basePath}editGroup?id=${groupTrove.id}">${groupTrove.recipeName}</a> (${len(groupTrove.listTroves())} troves)
                    </li>

                    <li py:if="groupTrove">
                        All packages you select by clicking on the
                        package's "Add this package" link will be added to
                        this group.
                    </li>
                </ul>

                <h2>Other Groups</h2>

                <p>To stop building the current group and start building
                another, click on the desired group.</p>

                <ul>
                    <li py:for="gt in groupTrovesInProject">
                        <a href="${basePath}editGroup?id=${gt[0]}">${gt[1]} <span py:if="groupTrove and groupTrove.id == gt[0]">(currently selected)</span></a>
                    </li>
                </ul>
                <a href="${basePath}newGroup"><b>Create a new group</b></a>
            </div>
        </div>
    </body>
</html>
