<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint.helperfuncs import formatProductVersion, truncateForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid', 'packagecreator.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Create Package: %s' % project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu(readOnlyVersion=True)}
            </div>
            
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                </div>

                <div id="middle">
                    ${productVersionMenu(readOnly=True)}
                    <p py:if="message" class="message" py:content="message"/>
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div class="page-title">
                    Package Creator<span py:if="name" py:strip="True"> - Editing ${name.replace(':source', '')}</span></div>
                    <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/whizzyupload.js?v=${cacheFakeoutVersion}" />
                    ${createPackage(uploadDirectoryHandle, sessionHandle, name, 'If you have an archive of binary software you would like package for %s, you can package it here.' % project.getNameForDisplay())}
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
