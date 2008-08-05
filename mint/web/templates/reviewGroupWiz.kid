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
              <h2>Appliance Creator - Review</h2>
              <h3>Added Troves</h3>
              <div py:if="explicitTroves">
              <ul>
                <li py:for="trove in explicitTroves">
                  ${trove}
                </li>
              </ul>
              <h2>Next Steps</h2>
              <ul>
                <li><a href="newPackage">Create a new package</a></li>
                <li><a href="buildApplianceGroup">Build appliance</a></li>
              </ul>
              </div>
              <div py:if="not explicitTroves">
                No troves selected
              <h2>Next Steps</h2>
              <ul>
                <li><a href="editApplianceGroup">Select packages</a></li>
                <li><a href="newPackage">Create a new package</a></li>
              </ul>
              </div>
            </div>
        </div>
    </body>
</html>

