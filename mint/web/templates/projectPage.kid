<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.mint import upstream, extractIs
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
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">${project.getName()}</a>
    </div>

    <head>
        <title>${formatTitle("Project Page: %s"%project.getName())}</title>
    </head>
    <body>
        <td id="content">
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="left" class="side">
                        <div class="pad">
                            ${projectResourcesMenu()}
                            <div class="palette" id="releases">
                                <h3>
                                    <a href="${basePath}rss" class="rssButton">
                                        <img src="${cfg.staticPath}/apps/mint/images/xml.gif"/>
                                    </a>
                                    Recent Releases
                                </h3>
                                <ul>
                                    <?python releases = project.getReleases() ?>
                                    <li class="release" py:if="releases" py:for="release in releases">
                                        <a href="${basePath}release?id=${release.getId()}">
                                            Version ${upstream(release.getTroveVersion())} for ${release.getArch()}
                                        </a>
                                    </li>
                                    <li class="release" py:if="not releases">
                                        No Releases
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </td>
                    <td id="main">
                        <div class="pad">
                            <h2>${project.getName()}  <a py:if="isOwner" href="${basePath}editProject">Edit</a></h2>
                            <h3 py:if="project.getProjectUrl()">Project Home Page &#160;</h3>
                            <p py:if="project.getProjectUrl()"><a href="${project.getProjectUrl()}" py:content="project.getProjectUrl()" />
                            </p>
                            <h3>
                                Description &#160;
                            </h3>
                            <p py:for="line in project.getDesc().splitlines()">
                                ${line}
                            </p>
                            <p py:if="not project.getDesc()">The project owner has not entered a description</p>
                            <h3>Configuration</h3>

                            <p>
                                To add this project in your Conary configuration, add <tt><strong>${project.getLabel()}</strong></tt> 
                                to the <tt><strong>installLabelPath</strong></tt> line in the <tt><strong>/etc/conaryrc</strong></tt> (or your <tt><strong>~/.conaryrc</strong></tt>) file.</p>

                            <hr py:if="isDeveloper or not memberList or bool(auth.authorized) ^ bool(isOwner)" />
                            <p py:if="isDeveloper">
                                <em class="resign">You are a developer of this project.</em>
                                <a href="resign">Resign</a>
                            </p>
                            <p py:if="auth.authorized and not isOwner and not isDeveloper and memberList">
                                <em py:if="not userHasReq" class="resign">You are not a member of this project.</em>
                                <em py:if="userHasReq" class="resign">Your request to join this project is pending.</em>
                                <a py:if="not userHasReq" href="joinRequest">Request to join</a>
                                <a py:if="userHasReq" href="joinRequest">Modify your comments</a>
                            </p>
                            <p py:if="not memberList">
                                <em class="resign">This project is orphaned.</em>
                                <a py:if="auth.authorized" href="${basePath}adopt">Adopt this project</a>
                                <span py:strip="True" py:if="not auth.authorized">Log in to adopt this project.</span>
                            </p>
                        </div>
                    </td>
                    ${projectsPane()}
                </tr>
            </table>
        </td>
    </body>
</html>
