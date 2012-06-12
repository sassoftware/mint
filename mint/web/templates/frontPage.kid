<?xml version='1.0' encoding='UTF-8'?>
<?python
import time
from mint import userlevels
from mint import searcher
from mint import buildtypes
from mint.helperfuncs import truncateForDisplay
from mint.client import upstream
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Front Page')}</title>
    </head>
    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
        
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            <div id="frontPageBlockContainer">
                <div py:if="frontPageBlock">
                    <!-- Marketing block start -->
                    ${XML(frontPageBlock)}
                    <!-- Marketing block end -->
                </div>
                <img py:if="not frontPageBlock" src="${cfg.staticPath}/apps/mint/images/default-splash.jpg" />
            </div>
            <br class="clear" />
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"></div>
        </div>
        <div class="spacer"></div>
        <div class="fullpage_blue">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_topright.png" alt="" />
        
            <br class="clear" />
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_blue_bottomright.png" alt="" />
            <div class="bottom"></div>
        </div>
    </body>
</html>
