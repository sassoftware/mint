<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (C) 2005 rPath, Inc.
# All Rights Reserved
#
from mint import jobstatus
from mint import userlevels
from mint.mint import upstream
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
    <?python
    isOwner = (userLevel == userlevels.OWNER or auth.admin)
    if isOwner:
        onload = "setTimeout('getReleaseStatus(" + str(release.getId()) + ")', 1000);"
    else:
        onload = None

    bodyAttrs = {'onload': onload}
    ?>
    <head>
        <title>${formatTitle('Project Release')}</title>
    </head>
    <body py:attrs="bodyAttrs">
        <?python
            if isOwner:
                job = release.getJob()
            else:
                job = None

            if job and job.getStatus() > jobstatus.RUNNING:
                editOptionsStyle = ""
                editOptionsDisabledStyle = "color: gray; font-style: italic; display: none;"
            else:
                editOptionsStyle = "display: none;"
                editOptionsDisabledStyle = "color: gray; font-style: italic;"

             
            files = release.getFiles()
            published = release.getPublished()

        ?>
        <div py:def="breadcrumb()" py:strip="True">
            <a href="$basePath">${project.getName()}</a>
            <a href="${basePath}releases">Releases</a>
            <a href="#">Release: ${name}</a>
        </div>
    
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br/>Release: ${name} <span py:if="release.getPublished()">(published)</span></h2>

                <h3>Version ${upstream(version)} of ${trove} for ${release.getArch()}</h3>

                <ul id="downloads">
                    <li py:for="i, file in enumerate(files)">
                        <a href="${cfg.basePath}downloadImage/${file[0]}/${file[1]}">Download ${file[2] and file[2] or "Disc " + str(i+1)}</a>
                    </li>
                    <li py:if="not files">Release has no files.</li>
                </ul>

                <div py:strip="True" py:if="isOwner">
                    
                    <h3>Description</h3>
                    <p>${release.getDesc() or "Release has no description."}</p>
                    
                    <h3>Image Generation Status:</h3>

                    <p id="jobStatus">Retrieving job status...</p>

                    <h3>Options</h3>
                    <ul id="editOptions" py:attrs="{'style': editOptionsStyle}">
                        <li>
                            <a href="${basePath}editRelease?releaseId=${release.getId()}">Edit Release</a>
                        </li>
                        <li>
                            <a href="${basePath}restartJob?releaseId=${release.getId()}">Re-generate Release</a>
                        </li>
                        <li py:if="not release.getPublished() and files">
                            <a href="publish?releaseId=${release.getId()}">Publish Release</a>
                        </li>
                    </ul>
                    <ul id="editOptionsDisabled" py:attrs="{'style': editOptionsDisabledStyle}">
                        <li>Edit Release</li>
                        <li>Re-generate Release</li>
                        <li>Publish Release</li>
                    </ul>
                </div>
            </div>
        </td>
        ${projectsPane()}
    </body>
</html>
