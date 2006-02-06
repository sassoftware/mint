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
            <div id="right" class="side">
                ${resourcePane()}
                ${groupTroveBuilder()}
            </div>
            <div id="middle">
                <h1>${project.getNameForDisplay(maxWordLen = 50)} <span id="editProject" py:if="isOwner"><a href="${basePath}editProject">edit project</a></span></h1>
                <h2 py:if="project.getProjectUrl()">Project Home Page &#160;</h2>

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

                <p py:if="project.getProjectUrl()"><a href="${project.getProjectUrl()}" py:content="project.getProjectUrl()" />
                </p>
                <h3>Description</h3>
                <p py:for="line in project.getDesc().splitlines()">
                    ${line}
                </p>
                <p py:if="not project.getDesc()">The project owner has not entered a description.</p>
                <hr />
                <h3>What can I do with this project?</h3>

                <p>This is ${isOwner and "your" or "the"} project's home page.
                        <span py:strip="True" py:if="isOwner">Here, you can communicate
                        to your users the description or goal for your project.
                        Do this by clicking on the "Edit Project" link next to the
                        project name.</span>
                        <span py:strip="True" py:if="not isOwner">Here, you can read the
                        description or goal for this project.</span>
                </p>

                <p>From here you can use the left-hand tabs to:</p>
                <ul>
                        <li py:if="isOwner">Create, edit, and publish a project release</li>
                        <li py:if="not isOwner">Download an official project release</li>
                        <li>Browse the packages included in ${isOwner and "your" or "this"} project</li>
                        <li py:if="isOwner">Add or remove developers working on your project</li>
                        <li py:if="not isOwner">List the developers working on this project
                            <span py:strip="True" py:if="not (isOwner or isDeveloper)">and request to join them</span>
                        </li>
                        <li py:if="isOwner">Create and manage your project's mailing lists</li>
                        <li py:if="not isOwner">Join the mailing lists for this project or browse their archives</li>
                        <li>
                            Subscribe to release news
                            <a href="${basePath}rss">
                                <img style="border: none; vertical-align: middle;"
                                     src="${cfg.staticPath}apps/mint/images/rss-inline.gif" />
                            </a>
                        </li>

                </ul>

                <p>
                    For detailed information on building or installing software
                    for ${isOwner and "your" or "this"} project, check out:
                </p>
                <ul>
                    <li py:if="isOwner or isDeveloper">
                        <a href="${basePath}conaryDevelCfg">Setting up ${isOwner and "your" or "the"} project build environment</a>
                    </li>
                    <li><a href="${basePath}conaryUserCfg">Installing packages from ${isOwner and "your" or "this"} project</a></li>
                </ul>
            </div>
        </div>
    </body>
</html>
