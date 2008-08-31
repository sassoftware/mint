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
        <title>${formatTitle('Review Appliance Contents: %s' % project.getNameForDisplay())}</title>
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
              <h2>Review Appliance Contents</h2>
              <p>The packages you have created and/or selected appear below. If you are satisfied, click the "Build Appliance" button to continue; otherwise, use the links to make the desired changes.</p>
              <h3>Added Packages</h3>
              <div py:if="explicitTroves">
              <ul class="unnestedList">
                <li py:for="trove in explicitTroves">
                  ${trove}
                </li>
              </ul>
              <a class="option" href="buildApplianceGroup">Build Appliance</a>
              <p><a href="newPackage">Package more files</a></p>
              <p><a href="selectPackages">Select additional packages</a></p>
              <p><a href="editApplianceGroup">Edit appliance contents</a></p>
              </div>
              <div py:if="not explicitTroves">
                No packages added
              <p><a href="newPackage">Package more files</a></p>
              <p><a href="selectPackages">Select additional packages</a></p>
              </div>
            </div>
        </div>
    </body>
</html>

