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
              ${buildPackage(sessionHandle, type="Package", helpText="Your files are now being packaged. Depending on the number of files, this process may take some time.")}
                <!-- The following are displayed based on whether the build was
                     successful or not -->
              <div id="build_success" style="display:none">
                  <p>Your files have been successfully packaged. You can now either package more files, or continue the appliance creation process.</p>
                  <p><a href="selectPackages">Continue</a></p>
                  <p><a href="newPackage">Package more files</a></p>
              </div>
              <div id="build_fail" style="display:none">
                  <p>Your files could not be packaged. You can review the package details, or package more files.</p>
                  <p><a href="javascript: history.go(-1);">Review package details</a></p>
                  <p><a href="newPackage">Package more files</a></p>
              </div>
            </div>
        </div>
    </body>
</html>
