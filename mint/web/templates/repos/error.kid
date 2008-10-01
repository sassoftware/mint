<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
 Copyright (c) 2005-2007 rPath, Inc.

 All Rights Reserved
-->
    <head>
        <title>${formatTitle('Repository Error')}</title>
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
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Error</div>
                    <pre class="error">${error}</pre>
                    <p>Please go back and try again.</p>
                </div>
                <br class="clear" />
                <img src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
