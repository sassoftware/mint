<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.mint import upstream 
?>
<html xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved 
-->
    <?python
        isOwner = (userLevel == userlevels.OWNER or auth.admin)
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()

        releases = project.getReleases()
        commits = project.getCommits()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">${project.getName()}</a>
    </div>

    <head>
        <title>${formatTitle("Project Page: %s"%project.getName())}</title>
        <link py:if="releases" rel="alternate" type="application/rss+xml"
              title="${project.getName()} Releases" href="${basePath}rss" />

    </head>
    <body>
        <td id="content">
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="left" class="side">
                        <div class="pad">
                            ${projectResourcesMenu()}
                            ${releasesMenu(releases, isOwner)}
                            ${commitsMenu(commits)}
                            ${browseMenu(display='none')}
                            ${searchMenu(display='none')}
                        </div>
                    </td>
                    <td id="main">
                        <div class="pad">


                            <h2>${project.getName()}</h2>
                            <h3 py:if="project.getProjectUrl()">Project Home Page &#160;</h3>
                            <p py:if="project.getProjectUrl()"><a href="${project.getProjectUrl()}" py:content="project.getProjectUrl()" />
                            </p>
                            <h3>Description</h3>
                            <p py:for="line in project.getDesc().splitlines()">
                                ${line}
                            </p>
                            <p py:if="not project.getDesc()">The project owner has not entered a description</p>

                            <hr />
                            <h4>What can I do with this project?</h4>
                            <ul>
                                <li py:if="isOwner">
                                    <a href="${basePath}editProject">Edit project details</a>
                                </li>
                                <li py:if="releases">
                                    <a href="${basePath}rss">
                                        subscribe to release news 
                                            <img style="border: none; vertical-align: middle;"
                                                 src="${cfg.staticPath}apps/mint/images/xml.gif" />
                                    </a>
                                </li>
                                <li>
                                    <a href="${basePath}conaryCfg">Add to my conary setup</a>
                                </li>
                                <li py:if="auth.authorized and userLevel == userlevels.NONMEMBER">
                                    <a href="${basePath}watch">Watch this project</a>
                                </li>
                                <li py:if="userLevel == userlevels.USER">
                                    <a href="${basePath}unwatch">Stop watching this project</a>
                                </li>
                                <div py:strip="True" py:if="not project.external">
                                    <li py:if="isDeveloper"><a href="resign">Resign from this project</a></li>
                                    <li py:if="auth.authorized and not isOwner and not isDeveloper and memberList">
                                        <a py:if="not userHasReq" href="joinRequest">Request to join this project</a>
                                        <a py:if="userHasReq" href="joinRequest">Modify your comments to a pending join request</a>
                                    </li>
                                    <li py:if="not memberList">
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
                    </td>
                    ${projectsPane()}
                </tr>
            </table>
        </td>
    </body>
</html>
