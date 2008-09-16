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
              
                <h2>Edit Appliance Contents</h2>
                <p>The packages that will be built into your appliance appear below. Make any desired changes to the list of packages, and click the "Update Contents" button to continue; otherwise, use the links to make the desired changes.</p>
                <div py:if="packageList" py:strip="True">
                <form name="packagecreatortroves" action="processEditApplianceGroup" method="post">
                    <ul class="package-checklist">
                        <li py:for="troveName in sorted(packageList, key=lambda x: x.upper())">
                        <?python
                            pkgname = troveName.replace(':source', '')
                        ?>
                        <input type="checkbox" name="troves" id="trove_${pkgname}" value="${pkgname}" checked="checked"/> <label for="trove_${pkgname}">${pkgname}</label>
                        </li>
                    </ul>
                    <input value="Confirm Contents" type="submit"/>
                    <p><a href="newPackage">Package another archive</a></p>
                    <p><a href="selectPackages">Select additional packages</a></p>
                </form>
                </div>
                
                <div py:if="not packageList" py:strip="True">
                    <!-- handle the no troves case -->
                    <p><img src="${cfg.staticPath}/apps/mint/images/errors.gif" alt="" /><strong>No content selected for your appliance</strong></p>
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
