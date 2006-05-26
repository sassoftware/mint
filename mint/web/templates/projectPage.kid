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
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <?python
        isOwner = (userLevel == userlevels.OWNER or auth.admin)
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()

        releases = project.getReleases(showUnpublished = False)
        commits = project.getCommits()

        if cfg.SSL:
            proto = "https"
        else:
            proto = "http"
    ?>
    <head>
        <title>${formatTitle("Project Page: %s"%project.getNameForDisplay())}</title>
        <link py:if="releases" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />

    </head>
    <body>
        <div id="layout">

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
                <h1>${project.getNameForDisplay(maxWordLen = 25)} <span id="editProject" py:if="isOwner"><a href="${basePath}editProject">edit project</a></span></h1>
                <div py:if="auth.admin" py:strip="True">

                    <h2>Project Status</h2>

                    <p>Project was created ${timeDelta(project.timeCreated, capitalized=False)}.</p>
                    <p py:if="project.hidden">This project is hidden.</p>
                    <p py:if="project.external">This project is externally managed.</p>
                    <p py:if="not (commits or project.external)">This project is considered to be a fledgling (i.e. no software has been committed to its repository).</p>

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

                <p class="help" py:if="not (commits or project.external) and cfg.hideFledgling and not auth.admin">
                    This is a fledgling project. The developers of this project
                    have not yet committed software into the project's repository.
                    To give the project's developers time to get started before
                    becoming fully visible to the rest of the rBuilder Online
                    community, fledgling projects do not appear on "Browse Projects"
                    pages (but will appear in search results). When software has been
                    committed into this project's repository, it will no longer be
                    considered fledgling, and will appear on "Browse Projects" pages.
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
                <h2>What can I do with this project?</h2>

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
                    for ${isOwner and "your" or "this"} project, check out the
                    project's <a href="${project.getUrl()}help">help
                    pages</a>.
                </p>
            </div>
        </div>
    </body>
</html>
