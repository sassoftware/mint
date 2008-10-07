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
        <title>${formatTitle('Create Appliance Manifest: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div id="left" class="side">
                ${wizard_navigation()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            
            <div id="fullpage-middle">
                
                <div class="edit-version">
                    Version: ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</div>
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>    
                <div class="page-title">Appliance Creator</div>   
              
                <p py:if="message" class="message" py:content="message"/>
             
                ${buildPackage(applianceSessionHandle, "Appliance Group", "The manifest that defines your appliance is now being created. Depending on the number of packages your appliance contains, this process may take some time.")}
                <!-- The following are displayed based on whether the build was
                     successful or not -->
                <div id="build_success" style="display:none">
                    <p>The manifest for your appliance has been successfully created.  Click the "Generate Appliance Images" button to continue.</p>
                    <p><a class="option" href="generateImages">Generate Appliance Images</a></p>
                </div>
                <div id="build_fail" style="display:none">
                    <p>The manifest for your appliance could not be created. Select from the following links to continue.</p>
                    <p><a href="newPackage">Package another archive</a></p>
                    <p><a href="selectPackages">Select additional packages</a></p>
                    <p><a href="editApplianceGroup">Edit appliance contents</a></p>
                </div>
            </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>