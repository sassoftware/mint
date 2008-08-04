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
        <title>${formatTitle('Edit Appliance Group Contents: %s' % project.getNameForDisplay())}</title>
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
              <h2>Appliance Creator - Editing Appliance Group</h2>
              <div py:if="packageList" py:strip="True">
              <form name="packagecreatortroves" action="processEditGroup" method="post">
              <ul>
                <li py:for="troveName in sorted(packageList.keys())">
                    <?python
                    pkgname = troveName.replace(':source', '')
                    ?>
                    <input type="checkbox" name="troves" id="trove_${pkgname}" value="${pkgname}" py:attrs="{'checked': (pkgname in selected) and 'checked' or None}"/> <label for="trove_${pkgname}">${pkgname}=${packageList[troveName]['develStageLabel']}</label>
                </li>
              </ul>
              <input value="Submit" type="submit"/>
              </form>
              </div>
              <div py:if="not packageList" py:strip="True">
                <h2>Additional Options</h2>
                <ul>
                  <li><a href="newPackage">Add a new package</a></li>
                </ul>
              </div>
            </div>
        </div>
    </body>
</html>
