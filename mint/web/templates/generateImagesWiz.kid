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
        <div id="layout">
            <div id="left" class="side">
                ${wizard_navigation()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)} - Version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</h1>
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
        </div>
    </body>
</html>
