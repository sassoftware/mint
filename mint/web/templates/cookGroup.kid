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

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getNameForDisplay()}</a>
        <a href="#">Group Builder</a>
    </div>

    <body onload="getCookStatus(${jobId});">
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h1 id="pleaseWait">Cooking Your Group</h1>

                <p>Your request to cook ${groupTrove.recipeName} has been
                submitted.</p>

                <h2>Request Status: <span id="jobStatus"> </span></h2>
 
                <p>When the request status "Finished" appears, your group
                has finished cooking. Click on the "Releases" link in the
                "Project Resources" sidebar, and select
                ${groupTrove.recipeName} to create a release.</p>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
        </td>
    </body>
</html>
