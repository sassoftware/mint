<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <head>
        <title>${formatTitle('Published Releases: %s' % project.getNameForDisplay())}</title>
        <link py:if="releases" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />
    </head>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER or auth.admin
    ?>

    <div py:def="pubReleasesTable(releases, isOwner)">
        <table>
            <tbody>
                <tr py:for="release in releases">
                    <td>${release.name}</td>
                    <td>${release.version}</td>
                    <td>(<a href="${basePath}release/${release.id}">view</a>)</td>
                </tr>
            </tbody>
        </table>
    </div>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                <h2>Releases</h2>
                <div py:if="releases">
                    ${pubReleasesTable(releases, isOwner)}
                </div>
                <div py:if="not releases">
                    This project currently has no releases.
                </div>
                <div py:if="isOwner">
                    <a href="createRelease">Create a new release</a>
                </div>
            </div>
        </div>
    </body>
</html>
