<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Build Packages: %s' % project.getNameForDisplay())}</title>
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
                    ${productVersionMenu()}
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Maintain Packages</div>
                
                    <p py:if="message" class="message" py:content="message"/>
                    
                    <h2>Available Source Packages</h2>

                    <div py:for="pkg in pkgList">
                        <form name="build-form-pkg[0]" action="buildSourcePackage" method="POST">
                            ${pkg[0].replace(':source','')} version ${pkg[1].trailingRevision()}
                            <input type="hidden" name="troveName" value="${pkg[0]}"/>
                            <input type="hidden" name="troveVersion" value="${str(pkg[1])}"/>
                            <input type="submit" value="Build"/>
                        </form>
                    </div>

                </div><!--middle-->
                <br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div><!--layout-->
    </body>
</html>
