<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved 
-->
    <?python
        isOwner = userLevel == userlevels.OWNER
        isDeveloper = userLevel == userlevels.DEVELOPER
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">${project.getName()}</a>
    </div>

    <head>
        <title>rpath.org: ${project.getName()}</title>
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
                                    <a href="/rss" class="rssButton">
                                        <img src="${cfg.staticUrl}/apps/mint/images/xml.gif"/>
                                    </a>
                                    Recent Releases
                                </h3>
                                <ul>
                                    <li class="release" py:for="release in project.getReleases()">
                                        <a href="/release?id=${release.getId()}">
                                            ${release.getTroveName()} = ${release.getTroveVersion().trailingRevision().asString()}
                                        </a>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </td>
                    <td id="main">
                        <div class="pad">
                            <h2>${project.getName()}</h2>
                            <h3>
                                Description &#160; <a py:if="isOwner" href="projectDesc">Edit</a>
                            </h3>
                            <p py:for="line in project.getDesc().splitlines()">
                                ${line}
                            </p>
                            <p py:if="not project.getDesc()">The project owner has not entered a description</p>
                            <h3>Configuration</h3>

                            <p>
                                To add this project in your Conary configuration, add <tt><strong>${project.getLabel()}</strong></tt> 
                                to the <tt><strong>installLabelPath</strong></tt> line in the <tt><strong>/etc/conaryrc</strong></tt> (or your <tt><strong>~/.conaryrc</strong></tt>) file.</p>

                            <hr/>
                            <p py:if="isDeveloper">
                                <em class="resign">You are a developer of this project.</em>
                                <a href="resign">Resign</a>
                            </p>
                            <p py:if="not memberList">
                                <em class="resign">This project is orphaned.</em>
                                <a py:if="auth.authorized" href="adopt">Adopt this project</a>
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
