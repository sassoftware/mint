<?xml version='1.0' encoding='UTF-8'?>
<?python
import simplejson
from mint.helperfuncs import truncateForDisplay, formatProductVersion
from mint.web.templatesupport import projectText

if 'message' not in locals():
    message = None

?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Appliance Creator: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="middle">
              <p py:if="message" class="message" py:content="message"/>
              <h1>${project.getNameForDisplay(maxWordLen = 50)} - Version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</h1>
              <h2>Appliance Creator</h2>

              <div class="mailingListButtons">
                <div py:for="troveName in sorted(groups.keys())" py:strip="True">
                  <?python
                  pkgname = troveName.replace(':source', '')
                  ?>
                  <h3>${pkgname}</h3>
                  <ul>
                    <li><a class="option" href="startApplianceCreator">Edit Appliance</a></li>
                  </ul>
                </div>
                <h3>Discard current appliance contents and start over</h3>
                <ul><li><a href="startApplianceCreator?maintain=0" class="option">Create Appliance</a></li>
                </ul>
              </div>
            </div>
        </div>
    </body>
</html>
