<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.client import timeDelta
from mint.client import upstream
from mint.helperfuncs import truncateForDisplay
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <?python
        if cfg.SSL:
            proto = "https"
        else:
            proto = "http"
    ?>
    <head>
        <title>${formatTitle("%s Page: %s"%(projectText().title(),project.getNameForDisplay()))}</title>
        <link rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />
        <link rel="alternate" type="application/rss+xml"
            title="${project.getName()} Commits" href="${basePath}rss?feed=commits" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/editversion.js?v=${cacheFakeoutVersion}"/>
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
                <h1>${project.getNameForDisplay(maxWordLen = 25)}</h1>

                ${downloadsMenu(latestBuildsWithFiles)}

                <div py:if="auth.admin" py:strip="True">

                    <h2>${projectText().title()} Status</h2>

                    <p>${projectText().title()} was created ${timeDelta(project.timeCreated, capitalized=False)}.</p>
                    <p py:if="vmtnId">This ${projectText().lower()} is listed on the <a href="http://www.vmware.com/vmtn/appliances/directory/${vmtnId}">VMware(R) Virtual Appliance Marketplace</a></p>
                    <p py:if="project.hidden">This ${projectText().lower()} is hidden.</p>
                    <p py:if="project.external and not auth.admin">This ${projectText().lower()} is externally managed.</p>
                    <p py:if="not (projectCommits or project.external)">This ${projectText().lower()} is considered to be a fledgling
                        (i.e. no software has been committed to its repository).</p>
                </div>
                
                <div py:if="isOwner" py:strip="True">
                    <h2>Manage This ${projectText().title()}</h2>
                    <ul>
                        <li><a href="${basePath}editProject">Edit</a> ${projectText().lower()} settings</li>
                        <li py:if="not external"><a href="${basePath}editVersion">Create</a> a new ${projectText().lower()} version</li>
                        <li py:if="versions and not external">
                            Edit ${projectText().lower()} version
                            <select py:attrs="{'id': 'version', 'name': 'version', 'class': 'field'}" onchange="editVersionRedirect('${basePath}', this.options[this.selectedIndex].value);">
                                <option py:if="versions" py:content="'--'" value="-1" selected="selected"/>
                                <option py:for="ver in versions" py:content="'%s %s' % (ver[2], ver[3])" value="${ver[0]}"/>
                            </select>
                        </li>
                    </ul>
                </div>
                <div py:if="isWriter" py:strip="True">
                    <h2>Add ${projectText().title()} Contents</h2>
                    <ul>
                        <li>Create a <a href="${basePath}newBuild">new image</a></li>
                        <li>Create a <a href="${basePath}newRelease">new release</a></li>
                        <li>Create a <a href="${basePath}newPackage">new package</a></li>
                    </ul>
                </div>
                <div py:if="auth.admin" py:strip="True">
                    <h2>Administrative Options</h2>

                    <p py:if="project.external">This ${projectText().lower()} is externally managed and cannot be administered from this interface.</p>
                    <form py:if="not project.external" action="${basePath}processProjectAction" method="post">
                        <label for="projectAdminOptions">Choose an action:&nbsp;</label>
                        <select id="projectAdminOptions" name="operation">
                            <option value="project_noop" selected="selected">--</option>
                            <option py:if="not project.hidden" value="project_hide">Hide ${projectText().title()}</option>
                            <option py:if="project.hidden" value="project_unhide">Unhide ${projectText().title()}</option>
                        </select>

                        <button id="projectAdminSubmitButton" type="submit">Go</button>
                        <input type="hidden" value="${project.getId()}" name="projectId" />
                    </form>
                </div>

                <p class="help" py:if="not (projectCommits or project.external) and cfg.hideFledgling and not auth.admin">
                    This is a fledgling ${projectText().lower()}. The developers of this ${projectText().lower()}
                    have not yet committed software into the ${projectText().lower()}'s repository.
                    To give the ${projectText().lower()}'s developers time to get started before
                    becoming fully visible to the rest of the rBuilder Online
                    community, fledgling ${projectText().lower()}s do not appear on "Browse ${projectText().title()}s"
                    pages (but will appear in search results). When software has been
                    committed into this ${projectText().lower()}'s repository, it will no longer be
                    considered fledgling, and will appear on "Browse ${projectText().title()}s" pages.
                </p>

                <p class="help" py:if="project.external and (not mirrored) and (not anonymous) and auth.admin">
                    To preload this external ${projectText().lower()} as a local mirror, please have the preload drive containing
                    the contents for <b>${project.getLabel().split("@")[0]}</b>, connected to the rBuilder server, and click
                    <a href="https://${cfg.hostName}.${cfg.siteDomainName}:8003/rAA/loadmirror/LoadMirror/">Load Mirror</a>.
                </p>

                <div py:if="project.getProjectUrl()" py:strip="True">
                <h2 py:if="project.getProjectUrl()">${projectText().title()} Home Page &#160;</h2>
                <p><a href="${project.getProjectUrl()}" py:content="truncateForDisplay(project.getProjectUrl(), maxWordLen=60)" /></p>
                </div>

                <h2>Description</h2>
                <p py:for="line in project.getDesc().splitlines()">
		    ${truncateForDisplay(line, 10000000, 70)}
                </p>
                <p py:if="not project.getDesc()">The ${projectText().lower()} owner has not entered a description.</p>
                <hr />
            </div>
        </div>
    </body>
</html>
