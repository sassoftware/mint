<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Group Trove Builder: %s' % project.getName())}</title>
    </head>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Group Trove Builder</a>
    </div>

    <body onload="getCookStatus(${jobId});">
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                ${browseMenu(display='none')}
                ${searchMenu(display='none')}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h1 id="pleaseWait">Cooking Group Trove</h1>
                <h2>Progress: <span id="jobStatus"> </span></h2>
 
                <pre style="padding: 1em; border: 1px solid #dddddd; background: #efefef; margin: 1em;">${XML(recipe.replace('\n', '&lt;br/&gt;'))}</pre>
                
                <p><i>[FIXME: improve wording and instructions]</i> When the group has finished cooking,
                    click on Releases on the left and pick ${groupTrove.recipeName} to create a release.</p>
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
