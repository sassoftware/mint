<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.mint import upstream
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <?python
        isOwner = (userLevel == userlevels.OWNER or auth.admin)
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()

        releases = project.getReleases(showUnpublished = False)
        commits = project.getCommits()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">${project.getNameForDisplay()}</a>
    </div>

    <head>
        <title>${formatTitle("Project Page: %s"%project.getNameForDisplay())}</title>
        <link py:if="releases" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />

    </head>
    <body>
        <div class="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(releases, isOwner)}
                ${commitsMenu(commits)}
            </div>
            <div id="main">
                <h2>${project.getNameForDisplay(maxWordLen = 50)}</h2>

                <p class="help" py:if="not commits and cfg.hideFledgling">
                    This is a fledgling project. The developers of this project
                    have not yet committed software into the project's repository.
                    To give the project's developers time to get started before
                    becoming fully visible to the rest of the rBuilder Online
                    community, fledgling projects do not appear on "Browse Projects"
                    pages (but will appear in search results). When software has been
                    committed into this project's repository, it will no longer be
                    considered fledgling, and will appear on "Browse Projects" pages.
                </p>

                <h3 py:if="project.getProjectUrl()">Project Home Page &#160;</h3>
                <p py:if="project.getProjectUrl()"><a href="${project.getProjectUrl()}" py:content="project.getProjectUrl()" />
                </p>
                <h3>Description</h3>
                <p py:for="line in project.getDesc().splitlines()">
                    ${line}
                </p>
                <p py:if="not project.getDesc()">The project owner has not entered a description</p>

                <div style="clear: left; border-top: 2px dotted #aaaaaa;">
                    <h4>What can I do with this project?</h4>
                    <ul>
                        <li py:if="isOwner">
                            <a href="${basePath}editProject">Edit project details</a>
                        </li>
                        <li py:if="releases">
                            <a href="${basePath}rss">
                                Subscribe to release news
                                    <img style="border: none; vertical-align: middle;"
                                         src="${cfg.staticPath}apps/mint/images/xml.gif" />
                            </a>
                        </li>
                        <li>
                            <a href="${basePath}conaryUserCfg">Install software on my Conary-based system</a>
                        </li>
                        <li py:if="isOwner or isDeveloper">
                            <a href="${basePath}conaryDevelCfg">Set up my Conary development environment</a>
                        </li>
                        <li py:if="auth.authorized and userLevel == userlevels.NONMEMBER">
                            <a href="${basePath}watch">Watch this project</a>
                        </li>
                        <li py:if="userLevel == userlevels.USER">
                            <a href="${basePath}unwatch">Stop watching this project</a>
                        </li>
                        <div py:strip="True" py:if="not project.external">
                            <li py:if="isDeveloper"><a href="${basePath}resign">Resign from this project</a></li>
                            <li py:if="auth.authorized and not isOwner and not isDeveloper and True in [ x[2] not in userlevels.READERS for x in memberList]">
                                <a py:if="not userHasReq" href="${basePath}joinRequest">Request to join this project</a>
                                <a py:if="userHasReq" href="${basePath}joinRequest">Modify your comments to a pending join request</a>
                            </li>
                            <li py:if="True not in [ x[2] not in userlevels.READERS for x in memberList]">
                                <a py:if="auth.authorized" href="${basePath}adopt">Adopt this project</a>
                                <span py:strip="True" py:if="not auth.authorized">Log in to adopt this project</span>
                            </li>
                            <li py:if="not auth.authorized">
                                Log in to:
                                    <li>Watch this project</li>
                                    <li>Request to join this project</li>
                            </li>
                        </div>
                    </ul>
                </div>
            </div>
        </div>
    </body>
</html>
