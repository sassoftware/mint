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
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">${project.getName()}</a>
    </div>

    <head/>
    <body>
        <td id="content">
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="left" class="side">
                        <div class="pad">
                            ${projectResourcesMenu()}
                            <div class="palette" id="releases">
                                <h3>Recent Releases</h3>
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
                            <p py:if="isOwner"><em>You are an owner of this project.</em></p>
                            <p py:if="not memberList">This project is orphaned. <a py:if="auth.authorized" href="adopt">Adopt this project</a><span py:strip="True" py:if="not auth.authorized">Log in to adopt this project</span>.</p>
                            <h3>
                                Description &#160;<span class="edit" py:if="isOwner">
                                <a href="projectDesc">Edit Description</a></span>
                            </h3>
                            <p>${project.getDesc()}</p>
                            <h3>Configuration</h3>

                            <p>To add this project in your Conary configuration, add the following to your ~/.conaryrc:</p>
                            <textarea style="width: 100%; white-space: nowrap;" readonly="readonly" rows="4">installLabelPath ${project.getLabel()}<p py:strip="True" py:if="auth.authorized">
repositoryMap ${project.getHostname()} http://${auth.username}:<i>password</i>@${project.getHostname()}/conary/</p></textarea>
                        </div>
                    </td>
                    ${projectsPane()}
                </tr>
            </table>
        </td>
    </body>
</html>
