<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (C) 2005 rpath, Inc.
# All Rights Reserved
#
from mint import jobstatus
from mint import userlevels
?>

<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
    <head/>
    <body onload="setTimeout('getReleaseStatus(${release.getId()})', 1000);">
        <?python
            preventEdit = job and job.getStatus() in (jobstatus.WAITING, jobstatus.RUNNING)
            files = release.getFiles()
            published = release.getPublished()
            isOwner = userLevel == userlevels.OWNER
        ?>
        
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br/>Release: ${name}</h2>

                <p>${trove}=${version.asString()} (architecture: ${release.getArch()})</p>

                <ul py:if="files">
                    <li py:for="i, file in enumerate(files)">
                        <a href="downloadImage?fileId=${file[0]}">Disc ${i+1}</a>
                    </li>
                </ul>

                <div py:strip="True" py:if="isOwner">
                    <p py:if="not preventEdit"><a href="editRelease?releaseId=${release.getId()}">Edit Release</a></p>
                    <p py:if="preventEdit" class="help">Release cannot be modified while it is being generated.</p>
                    
                    <h3>Description</h3>
                    <p>${release.getDesc() or "Release has no description."}</p>
                    
                    <h3>Image Generation Status:</h3>

                    <p id="jobStatus">Retrieving job status...</p>
                    <p>
                        <a href="restartJob?releaseId=${release.getId()}">Re-generate</a>
                        <a class="button" py:if="not release.getPublished()" href="publish?releaseId=${release.getId()}">Publish Image</a>
                    </p>
                    <p py:if="release.getPublished()">Image Published</p>
                </div>
            </div>
        </td>
        ${projectsPane()}
    </body>
</html>
