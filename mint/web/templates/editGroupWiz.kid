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
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div id="left" class="side">
                ${wizard_navigation()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            
            <div id="fullpage-middle">
                
                ${productVersionMenu(readOnly=True)}
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>    
                <div class="page-title">Appliance Creator</div>    
                
                <p py:if="message" class="message" py:content="message"/>
              
                <h2>Edit Appliance Contents</h2>
                <div py:if="packageList" py:strip="True">
                    <p>The packages that will be built into your appliance appear below. Make any desired changes to the list of packages, and click the "Update Contents" button to continue; otherwise, use the links to make the desired changes.</p>
                </div>
                <form id="packagecreatortroves" name="packagecreatortroves" action="processEditApplianceGroup" method="post">
                    <div py:if="packageList" py:strip="True">
                    <ul class="package-checklist">
                        <li py:for="troveName in sorted(packageList, key=lambda x: x.upper())">
                        <?python
                            pkgname = troveName.replace(':source', '')
                        ?>
                        <input type="checkbox" name="troves" id="trove_${pkgname}" value="${pkgname}" checked="checked"/> <label for="trove_${pkgname}">${pkgname}</label>
                        </li>
                    </ul>

                    ${recipeEditor('appliance', recipeContents, useOverrideRecipe, 'packagecreatortroves')}

                    <!-- XXX: this needs to be a graphical button -->
                    <input type="submit" id="packagecreatortrovessubmit" value="Confirm Contents" />
                    </div>
                
                    <div py:if="not packageList" py:strip="True">
                        <!-- handle the no troves case -->
                        <p>No packages have been added to your appliance</p>
                        <!-- XXX: this needs to be a graphical button -->
                        <input type="submit" id="packagecreatortrovessubmit" value="Continue" />
                    </div>
                    <p><a href="newPackage">Package another archive</a></p>
                    <p><a href="selectPackages">Select additional packages</a></p>
                </form>
            </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
