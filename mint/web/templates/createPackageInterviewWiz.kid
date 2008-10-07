<?xml version='1.0' encoding='UTF-8'?>
<?python
message = locals().get('message', None)
?>
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
                ${createPackageInterview(editing, sessionHandle, factories, prevChoices, recipeContents, useOverrideRecipe)}
            </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
      </div>
    </body>
</html>