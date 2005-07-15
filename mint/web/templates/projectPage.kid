<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved 
-->
    <?python
        isOwner = userLevel == userlevels.OWNER
        memberList = project.getMembers()
    ?>

    <div py:def="breadcrumb()" class="pad">
        You are here:
        <a href="#">rpath</a>
        <a href="#">${project.getName()}</a>
    </div>

    <head/>
    <body>
        <td id="content">
            <table border="0" cellspacing="0" cellpadding="0" summary="layout" width="100%">
                <tr>
                    <td id="left" class="side">
                        <div class="pad">
                            <div id="browse" class="palette">
                                <h3>Project resources </h3>
                                <ul>
                                    <li><a href="releases">Releases</a></li>
                                    <li><a href="http://${project.getHostname()}/conary/browse">Repository</a></li>                                                            <li py:if="memberList"><a href="members">Project Members</a></li>
                                    <li><a href="#">Mailing Lists</a></li>
                                    <li><a href="#">Bug Tracking</a></li>
                                </ul> 
                            </div>
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
                            <p py:if="not memberList">This project is orphaned. <a href="adopt">Adopt this project</a>.</p>
                            <h3>
                                Description &#160;<span class="edit" py:if="isOwner">
                                <a href="projectDesc">Edit Description</a></span>
                            </h3>
                            <p>${project.getDesc()}</p>
                        </div>
                    </td>
                    ${projectsPane()}
                </tr>
            </table>
        </td>
    </body>
</html>
