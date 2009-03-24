<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.client import timeDelta
from mint.client import upstream
from mint.helperfuncs import truncateForDisplay, formatProductVersion
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
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>
                <div id="middle">
                    ${productVersionMenu()}
                    <h1 class="primary">${project.getNameForDisplay(maxWordLen = 25)}</h1>
    
                    ${downloadsMenu(latestBuildsWithFiles)}
    
                    <p py:if="not (projectCommits or project.external) and cfg.hideFledgling and not auth.admin">This ${projectText().lower()} is considered to be a fledgling (i.e. no software has been committed to its repository).</p>
                    <div class="pageSection" py:if="isWriter or isReader">
    
                        <h2>${projectText().title()} Status</h2>
    
                        <p>${projectText().title()} was created ${timeDelta(project.timeCreated, capitalized=False)}.</p>
                        <p py:if="vmtnId">This ${projectText().lower()} is listed on the <a href="http://www.vmware.com/vmtn/appliances/directory/${vmtnId}">VMware(R) Virtual Appliance Marketplace</a></p>
                        <p py:if="project.hidden">This a private ${projectText().lower()}.</p>
                        <p py:if="not project.hidden">This a public ${projectText().lower()}.</p>
                        <p py:if="project.external and not auth.admin">This ${projectText().lower()} is externally managed.</p>
                    </div>
                    
                    <div class="pageSection" py:if="isOwner">
                        <h2>Manage This ${projectText().title()}</h2>
                        <ul class="pageSectionList">
                            <li><a href="${basePath}editProject">Edit</a> ${projectText().lower()} settings</li>
                            <li py:if="not external"><a href="${basePath}editVersion">Create</a> a new ${projectText().lower()} version</li>
                            <li py:if="versions and not external and currentVersion">
                                <a href="${basePath}editVersion?id=${currentVersion}">Edit</a> ${projectText().lower()} version ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}
                            </li>
                            <li py:if="not versions or not currentVersion">
                            Select a product version above to edit that version<span py:if="project.isAppliance" py:strip="True">, or manage the appliance</span>
                            </li>
                            <li py:if="versions and currentVersion and project.isAppliance"><a href="${cfg.basePath}apc/${project.shortname}/">Manage</a> the ${project.getNameForDisplay(maxWordLen=25)} ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)} appliance</li>
                            <li py:if="auth.admin and not external">
                                <a href="${basePath}deleteProject">Delete</a> this ${projectText().lower()}
                            </li>
                        </ul>
                    </div>
                    <div class="pageSection" py:if="isWriter">
                        <h2>Add ${projectText().title()} Contents</h2>
                        <ul class="pageSectionList">
                            <li>Create a <a href="${basePath}newBuild">New Image</a><span py:if="versions and currentVersion"> or a <a href="${basePath}newBuildsFromProductDefinition">New Image Set based on ${truncateForDisplay(formatProductVersion(versions, currentVersion), maxWordLen=30)}</a></span></li>
                            <li py:if="isOwner">Create a <a href="${basePath}newRelease">New Release</a></li>
                            <li>Create a <a href="${basePath}newPackage">New Package</a></li>
                        </ul>
                    </div>
                    <div class="pageSection" py:if="isWriter">
                        <h2>Maintain ${projectText().title()} Contents</h2>
                        <ul class="pageSectionList">
                            <li>Maintain <a href="${basePath}packageCreatorPackages">packages</a></li>
                        </ul>

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
                        <a href="https://${cfg.hostName}.${cfg.siteDomainName}:8003/loadmirror/LoadMirror/">Load Mirror</a>.
                    </p>
                    </div>
    
                    <div class="pageSection" py:if="project.getProjectUrl()">
                        <h2 py:if="project.getProjectUrl()">${projectText().title()} Home Page &#160;</h2>
                        <p>
                        <a href="${project.getProjectUrl()}" py:content="truncateForDisplay(project.getProjectUrl(), maxWordLen=60)" /></p>
                    </div>
                    
                    <div class="pageSection">
                        <h2>Description</h2>
                        <p py:for="line in project.getDesc().splitlines()">
    		            ${truncateForDisplay(line, 10000000, 70)}
                        </p>
                        <p py:if="not project.getDesc()">The ${projectText().lower()} owner has not entered a description.</p>
                    </div>
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
