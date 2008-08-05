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
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>

                <h2>Images</h2>
                <div py:if="isWriter">
                    You may:
                    <ul>
                        <li py:if="not project.external"><a href="newBuildsFromProductDefinition">Create a set of images for version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</a></li>
                        <li><a href="newBuild">Create a single image</a></li>
                    </ul>
                </div>
                <div py:if="builds" py:strip="True">
                ${buildsTable(builds)}
                </div>
                <p py:if="not builds">This ${projectText().lower()} contains no images.</p>
            </div>
        </div>
    </body>

</html>
