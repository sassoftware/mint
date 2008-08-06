<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Download Statistics: %s'%project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${productVersionMenu()}
                ${releasesMenu(projectPublishedReleases, isOwner)}
                ${commitsMenu(projectCommits)}
            </div>
            <div id="spanright">
                <img src="downloadChartImg?span=$span" /> 
            </div>
        </div>
    </body>
</html>
