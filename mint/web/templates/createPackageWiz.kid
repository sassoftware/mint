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
        <title>${formatTitle('Package Archive: %s' % project.getNameForDisplay())}</title>
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
            <h1>${project.getNameForDisplay(maxWordLen = 50)} - Version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</h1>
            <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/whizzyupload.js?v=${cacheFakeoutVersion}" />
            ${createPackage(uploadDirectoryHandle, sessionHandle, name, 'If you have an archive containing files you would like to add to your appliance, you can upload it and have its contents packaged for you. Otherwise, click the "No archive to package" link.')}
            <div>
              <a href="selectPackages">No archive to package</a>
            </div>
        </div>
        </div>
    </body>
</html>
