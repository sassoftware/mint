<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint.helperfuncs import formatProductVersion, truncateForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid', 'packagecreator.kid', 'wizard.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Edit Appliance Contents: %s' % project.getNameForDisplay())}</title>
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
              <h2>Edit Appliance Contents</h2>
              <p>The packages you have created and/or selected appear below. Make any desired changes to the list of packages, and click the "Update Contents" button to continue; otherwise, use the links to make the desired changes.</p>
              <div py:if="packageList" py:strip="True">
              <form name="packagecreatortroves" action="processEditApplianceGroup" method="post">
              <ul class="unnestedList">
                <li py:for="troveName in sorted(packageList, key=lambda x: x.upper())">
                    <?python
                    pkgname = troveName.replace(':source', '')
                    ?>
                    <input type="checkbox" name="troves" id="trove_${pkgname}" value="${pkgname}" checked="checked"/> <label for="trove_${pkgname}">${pkgname}</label>
                </li>
              </ul>
              <input value="Update Contents" type="submit"/>
              <p><a href="newPackage">Package more files</a></p>
              <p><a href="selectPackages">Select additional packages</a></p>
              </form>
              </div>
              <div py:if="not packageList" py:strip="True">
                <!-- handle the no troves case -->
                <h2>No content selected for your appliance</h2>
                  <p><a href="newPackage">Package more files</a></p>
                  <p><a href="selectPackages">Select additional packages</a></p>
              </div>
            </div>
        </div>
    </body>
</html>
