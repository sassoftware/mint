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
             
                <h2>Review Appliance Contents</h2>
                <div py:if="explicitTroves">
                    <p>The packages that will be built into your appliance appear below. If you are satisfied, click the "Build Appliance" button to continue; otherwise, use the links to make the desired changes.</p>
                    <div class="page-subtitle">Added Packages</div>
                    <ul class="package-checklist">
                        <li py:for="trove in explicitTroves">${trove}</li>
                    </ul>
                    <p><a class="option" href="buildApplianceGroup">Build Appliance</a></p>
                    <p><a href="newPackage">Package another archive</a></p>
                    <p><a href="selectPackages">Select additional packages</a></p>
                    <p><a href="editApplianceGroup">Edit appliance contents</a></p>
                </div>
                
                <div py:if="not explicitTroves">
                    <p>No custom packages have been added to your appliance. Click the "Build Appliance" button to continue; otherwise, use the links to make the desired changes.</p>
                    <p><a class="option" href="buildApplianceGroup">Build Appliance</a></p>
                    <p><a href="newPackage">Package another archive</a></p>
                    <p><a href="selectPackages">Select additional packages</a></p>
                </div>
            </div>
            <br class="clear"/>
            <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>

