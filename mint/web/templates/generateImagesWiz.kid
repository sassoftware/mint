<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint.helperfuncs import truncateForDisplay, formatProductVersion
from mint.web.templatesupport import projectText
from mint import buildtypes
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'builds_common.kid', 'wizard.kid'">
    <head>
        <title>${formatTitle('%s Image'%projectText().title())}</title>
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
                
                <h2>Generate Appliance Images</h2>
                <p>The following appliance image(s) are now being generated.  Refresh this page for updated status. When an image displays the "Finished" status, it is ready to be deployed.</p>

                <div py:if="builds" py:strip="True">
                    ${buildsTable(builds.values(), allowDelete=False)}
                </div>
                <div py:if="not builds" py:strip="True">
                    How did you get here?  I'd really like to know
                </div>
                <p><a href="${basePath}">Return to ${project.getNameForDisplay()} home</a></p>
                <p><a href="${basePath}builds">View all images</a></p>
            </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
