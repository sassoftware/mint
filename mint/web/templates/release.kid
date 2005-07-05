<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import jobstatus
import time
import textwrap
import os.path
from deps import deps
title = "Release Details"

?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">

    ${html_header(title)}
    <body onload='setTimeout("getReleaseStatus(${release.getId()})", 1000);'>
        ${header_image()}
        <?python
            m = menu([('All Releases', 'releases',  False),
                      ('Release Details', None, True)])

            preventEdit = job and job.getStatus() in (jobstatus.WAITING, jobstatus.RUNNING)
        ?>
        ${m}
        <div id="content">
            <h2>Release: ${name}</h2>

            <table class="bordered">
                <thead><tr>
                    <td colspan="2" style="font-weight: bold; font-size: 105%;">
                        <span style="float: left;">Trove: ${trove}=${version.asString()} (architecture: ${release.getArch()})</span>

                        <a py:if="not preventEdit" class="button" style="float: right;" href="editRelease?releaseId=${release.getId()}">Edit Release</a>
                        <span py:if="preventEdit" class="help" style="float: right">Release cannot be modified while it is being generated.</span>
                    </td>
                </tr></thead>
            </table>


            <table class="bordered">
                <thead><tr>
                    <td><span style="float: left;">Description:</span></td>
                </tr></thead>
                <tr><td>${release.getDesc()}</td></tr>
            </table>

            <table class="bordered">
                <tr>
                    <td class="tableheader" style="width: 15%;">Image Status:</td>
                    <td>
                        <span id="jobStatus" style="float: left;">Retrieving job status...</span>
                        <a style="float: right;" class="button"
                           href="restartJob?releaseId=${release.getId()}">Re-generate</a>

                        <a style="float: right; visibility: hidden;" class="button" id="downloads"
                           href="downloadImage?releaseId=${release.getId()}">
                            Download Images
                        </a>
                    </td>
                </tr>
            </table>
            <p>
                <a class="button" py:if="not release.getPublished()" href="publish?releaseId=${release.getId()}">Publish Image</a>
                <div py:if="release.getPublished()">Image Published</div>
            </p>

            ${html_footer()}
        </div>
    </body>
</html>
