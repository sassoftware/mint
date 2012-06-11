<?xml version='1.0' encoding='UTF-8'?>
<?python
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
            
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                </div>

                <div id="middle">

                    ${productVersionMenu(readOnly=True)}
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div class="page-title">Manage Appliance</div>
                    
                    <p py:if="message" class="message" py:content="message"/>
                    
                    <div class="pageSection">
                        <h2>Appliance Creator</h2>
                        <div class="inlineButtonList">
                            <p>This dialog will guide you through the steps necessary to package your software as an appliance.</p>
                            <p py:if="groups">Click the "Revise Appliance" button to make changes to your existing appliance, or click "Start Over" to start the appliance creation process from the beginning.</p>
                            <p py:if="not groups">Click the "Create Appliance" button to begin.</p>
                            <p py:if="groups">
                                <a class="no-decoration" href="startApplianceCreator">
                                    <img src="${cfg.staticPath}/apps/mint/images/revise_appliance_button.png" alt="" /></a>
                                <a href="startApplianceCreator?maintain=0">
                                    <img src="${cfg.staticPath}/apps/mint/images/start_over_button.png" alt="" /></a>
                            </p>
                            <p py:if="not groups">
                                <a href="startApplianceCreator?maintain=0">
                                    <img src="${cfg.staticPath}/apps/mint/images/create_appliance_button.png" alt="" /></a>
                            </p>
                        </div>
                    </div>
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
