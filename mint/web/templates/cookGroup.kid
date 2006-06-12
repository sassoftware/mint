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
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
		${builderPane()}
            </div>

            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2>Group Builder: ${curGroupTrove.recipeName}</h2>
                <h3>Cooking Your Group</h3>

                <p>Your request to cook ${curGroupTrove.recipeName} has been
                submitted.</p>

                <h3>Request Status</h3>
                <div>
                    <img src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" id="spinner" style="float: right;"/>
                    <div id="statusMessage" class="running" />
                </div>


                <p>When the request status "Finished" appears, your group
                has finished cooking. Click on the "Releases" link in the
                "Project Resources" sidebar, and select
                ${curGroupTrove.recipeName} to create a release.</p>
            </div>
        </div>
    </body>
</html>
