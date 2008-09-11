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
        <title>${formatTitle('Create Appliance: %s' % project.getNameForDisplay())}</title>
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
              <h2>Create Appliance</h2>

              <div class="inlineButtonList">
                <p>This dialog will guide you through the steps necessary to package your software as an appliance.</p>
                <p py:if="groups">Click the "Revise Appliance" button to make changes to your existing appliance, or click "Start Over" to start the appliance creation process from the beginning.</p>
                <p py:if="not groups">Click the "Create Appliance" button to begin.</p>
                <ul>
                  <li py:if="groups"><a class="option" href="startApplianceCreator">Revise Appliance</a></li>
                  <li><a href="startApplianceCreator?maintain=0" class="option"><span py:if="groups" py:strip="True">Start Over</span><span py:if="not groups" py:strip="True">Create Appliance</span></a></li>
                </ul>
              </div>
            </div>
        </div>
    </body>
</html>
