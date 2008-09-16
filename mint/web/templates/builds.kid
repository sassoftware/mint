<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker, projectText
from mint.helperfuncs import truncateForDisplay, formatProductVersion
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'builds_common.kid'">
    <head>
        <title>${formatTitle('Images: %s' % project.getNameForDisplay())}</title>
        <link py:if="builds" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Images" href="${basePath}rss" />
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(projectPublishedReleases, isOwner)}
                ${commitsMenu(projectCommits)}
            </div>
             <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>
                
                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Images</div>
                    
                    <div py:if="isWriter">
                        <ul class="pageSectionList">
                            <li py:if="not project.external"><a href="newBuildsFromProductDefinition">Create a set of images for version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</a></li>
                            <li><a href="newBuild">Create a single image</a></li>
                        </ul>
                    </div>
                    ${buildsTable(builds, publishedReleases = publishedReleases)}
                    <div class="pageSection" py:if="not builds">This ${projectText().lower()} contains no images.</div>
                </div><br class="clear" />
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>

</html>
