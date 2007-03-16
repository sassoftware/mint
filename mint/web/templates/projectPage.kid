<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.client import timeDelta
from mint.client import upstream
from mint.helperfuncs import truncateForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <?python
        if cfg.SSL:
            proto = "https"
        else:
            proto = "http"
    ?>
    <head>
        <title>${formatTitle("Project Page: %s"%project.getNameForDisplay())}</title>
        <link rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />
        <link rel="alternate" type="application/rss+xml"
            title="${project.getName()} Commits" href="${basePath}rss?feed=commits" />
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
                <h1>${project.getNameForDisplay(maxWordLen = 25)} <span id="editProject" py:if="isOwner"><a href="${basePath}editProject">edit project</a></span></h1>

                ${downloadsMenu(latestBuilds)}

                <div py:if="auth.admin" py:strip="True">

                    <h2>Project Status</h2>

                    <p>Project was created ${timeDelta(project.timeCreated, capitalized=False)}.</p>
                    <p py:if="vmtnId">This project is listed on the <a href="http://www.vmware.com/vmtn/appliances/directory/${vmtnId}">VMware(R) Virtual Appliance Marketplace</a></p>
                    <p py:if="project.hidden">This project is hidden.</p>
                    <p py:if="project.external and not auth.admin">This project is externally managed.</p>
                    <p py:if="not (projectCommits or project.external)">This project is considered to be a fledgling
                        (i.e. no software has been committed to its repository).</p>

                    <h2>Administrative Options</h2>

                    <p py:if="project.external">This project is externally managed and cannot be administered from this interface.</p>
                    <form py:if="not project.external" action="${basePath}processProjectAction" method="post">
                        <label for="projectAdminOptions">Choose an action:&nbsp;</label>
                        <select id="projectAdminOptions" name="operation">
                            <option value="project_noop" selected="selected">--</option>
                            <option py:if="not project.hidden" value="project_hide">Hide Project</option>
                            <option py:if="project.hidden" value="project_unhide">Unhide Project</option>
                        </select>

                        <button id="projectAdminSubmitButton" type="submit">Go</button>
                        <input type="hidden" value="${project.getId()}" name="projectId" />
                    </form>
                </div>

                <p class="help" py:if="not (projectCommits or project.external) and cfg.hideFledgling and not auth.admin">
                    This is a fledgling project. The developers of this project
                    have not yet committed software into the project's repository.
                    To give the project's developers time to get started before
                    becoming fully visible to the rest of the rBuilder Online
                    community, fledgling projects do not appear on "Browse Projects"
                    pages (but will appear in search results). When software has been
                    committed into this project's repository, it will no longer be
                    considered fledgling, and will appear on "Browse Projects" pages.
                </p>

                <p class="help" py:if="project.external and (not mirrored) and (not anonymous) and auth.admin">
                    To preload this external project as a local mirror, please have the preload drive containing
                    the contents for <b>${project.getLabel().split("@")[0]}</b>, connected to the rBuilder server, and click
                    <a href="https://${cfg.hostName}.${cfg.siteDomainName}:8003/rAA/loadmirror/LoadMirror/">Load Mirror</a>.
                </p>

                <div py:if="project.getProjectUrl()" py:strip="True">
                <h2 py:if="project.getProjectUrl()">Project Home Page &#160;</h2>
                <p><a href="${project.getProjectUrl()}" py:content="truncateForDisplay(project.getProjectUrl(), maxWordLen=60)" /></p>
                </div>

                <h2>Description</h2>
                <p py:for="line in project.getDesc().splitlines()">
		    ${truncateForDisplay(line, 10000000, 70)}
                </p>
                <p py:if="not project.getDesc()">The project owner has not entered a description.</p>
                <hr />
            </div>
        </div>
    </body>
</html>
