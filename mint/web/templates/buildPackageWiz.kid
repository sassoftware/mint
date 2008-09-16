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
         <div class="fullpage">
            <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
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
              
                ${buildPackage(sessionHandle, type="Package", helpText="Your archive is now being packaged. Depending on its size, this process may take some time.")}
                <!-- The following are displayed based on whether the build was
                     successful or not -->
                <div id="build_success" style="display:none">
                    <p>Your archive has been successfully packaged. You can now either package another archive, or continue the appliance creation process.</p>
                    <p><a href="selectPackages">Continue</a></p>
                    <p><a href="newPackage">Package another archive</a></p>
                </div>
                <div id="build_fail" style="display:none">
                    <p>Your archive could not be packaged. Select from the following links to continue.</p>
                    <p><a href="javascript: history.go(-1);">Review package details</a></p>
                    <p><a href="newPackage">Package another archive</a></p>
                </div>
            </div>
            <br class="clear"/>
            <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
