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

    <body onload="getCookStatus(${jobId});">
        <div class="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
		${groupTroveBuilder()}
            </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2>Group Builder: ${groupTrove.recipeName}</h2>
                <h3>Cooking Your Group</h3>

                <p>Your request to cook ${groupTrove.recipeName} has been
                submitted.</p>

                <h3>Request Status</h3>
                <p id="jobStatus">Retrieving cook status...</p>

                <p>When the request status "Finished" appears, your group
                has finished cooking. Click on the "Releases" link in the
                "Project Resources" sidebar, and select
                ${groupTrove.recipeName} to create a release.</p>
            </div>
        </div>
    </body>
</html>
