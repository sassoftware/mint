<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid', 'packagecreator.kid', 'wizard.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Create Package: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${wizard_navigation()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            <div id="middle">
              <p py:if="message" class="message" py:content="message"/>
              <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
              <h2>Appliance Creator - Build</h2>
              ${buildPackage(sessionHandle)}
                <!-- The following are displayed based on whether the build was
                     successful or not -->
              <div id="build_success" style="display:none">
                  <p>Your package has built successfully, and has been added to your appliance.</p>
                  <p><a href="newPackage">Create a new package</a></p>
                  <p><a href="editApplianceGroup">Edit appliance contents</a></p>
              </div>
              <div id="build_fail" style="display:none">
                  <p>Your package did not build successfully.</p>
                  <p><a href="javascript: history.go(-1);">Review package details</a></p>
                  <p><a href="newPackage">Create a new package</a></p>
              </div>
            </div>
        </div>
    </body>
</html>
