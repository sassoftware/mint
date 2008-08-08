<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid', 'packagecreator.kid', 'wizard.kid'">
<?python
from mint.helperfuncs import formatProductVersion, truncateForDisplay
?>
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
              <h1>${project.getNameForDisplay(maxWordLen = 50)} - Version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</h1>
              ${buildPackage(applianceSessionHandle, "Appliance Group", "The group that defines the %s version %s appliance and will now be built.  Depending on its contents, the process may take some time." % (project.getNameForDisplay(), formatProductVersion(versions, currentVersion)))}
                <!-- The following are displayed based on whether the build was
                     successful or not -->
              <div id="build_success" style="display:none">
                  <p>The group for the ${project.getNameForDisplay()} version ${formatProductVersion(versions, currentVersion)} appliance has built successfully.  Click the "Generate Appliance Images" button to generate images to continue.</p>
                  <h2>Next Step</h2>
                  <p><a class="option" href="generateImages">Generate Images</a></p>
              </div>
              <div id="build_fail" style="display:none">
                  <p>Your appliance group did not build successfully.</p>
                  <h2>Next Steps</h2>
                  <p><a href="newPackage">Create a new package</a></p>
                  <p><a href="editApplianceGroup">Edit appliance contents</a></p>
              </div>
            </div>
        </div>
    </body>
</html>
