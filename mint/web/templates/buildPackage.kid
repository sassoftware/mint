<?xml version='1.0' encoding='UTF-8'?>
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
                ${projectResourcesMenu()}
            </div>
            
            <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${resourcePane()}
                </div>
    
                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div class="page-title">Package Creator</div>
              
                    <p py:if="message" class="message" py:content="message"/>
                    ${buildPackage(sessionHandle, 'Package', 'Your package has been created and will now be built.  Depending on the software being packaged, the build process may take some time.')}
                    <!-- The following are displayed based on whether the build was successful or not -->
                    <div id="build_success" style="display:none">
                        <p>Your package has built successfully</p>
                        <p><a href="newPackage">Create a new package</a></p>
                    </div>
                    <div id="build_fail" style="display:none">
                        <p>Your package did not build successfully.</p>
                        <p><a href="javascript: history.go(-1);">Review package details</a></p>
                        <p><a href="newPackage">Create a new package</a></p>
                    </div>
                </div><br class="clear" />
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
