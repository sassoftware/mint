<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint import jobstatus
from mint.web.templatesupport import downloadTracker, projectText
from mint.helperfuncs import truncateForDisplay, formatProductVersion
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:strip="True" py:def="buildsTableRow(build, rowNumber, basePath, allowDelete, release=None)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            rowAttrs = { 'class': (rowNumber % 2) and 'odd' or 'even' }
        ?>
        <tr py:attrs="rowAttrs">
            <td colspan="2" class="buildName">
                <span><a href="${basePath}build?id=${build.id}">${truncateForDisplay(build.name)}</a></span>
                <span py:if="build.description">- ${truncateForDisplay(build.description)}</span>
                <span py:if="release" class="buildAssociated">
                    <br />Part of ${release and 'published' or 'unpublished'} release <a href="${basePath}release?id=${release.id}">${release.name} (Version ${release.version}) </a>
                </span>
            </td>
            <td class="buildShortStatus">${jobstatus.statusNames[build.getStatus()['status']]}</td>
        </tr>
        <tr py:attrs="rowAttrs">
            <td class="buildInfo">${build.getTroveName()}<br />${"%s/%s" % (build.getTroveVersion().trailingLabel(), build.getTroveVersion().trailingRevision())}</td>
            <td py:if="build.getBuildType() != buildtypes.IMAGELESS" class="buildInfo">${build.getArch()}&nbsp;${buildtypes.typeNamesShort.get(build.getBuildType(), 'Unknown')}</td>
            <td py:if="build.getBuildType() == buildtypes.IMAGELESS" class="buildInfo">&nbsp;${buildtypes.typeNamesShort.get(build.getBuildType(), 'Unknown')}</td>
            <td class="buildInfo">&nbsp;<input py:if="not release and allowDelete" style="float: right;" name="buildIdsToDelete" type="checkbox" value="${build.id}" />
            </td>
        </tr>
    </div>

    <div py:strip="True" py:def="_buildsTable(builds, publishedReleases, basePath, allowDelete)">
        <table py:if="builds" border="0" cellspacing="0" cellpadding="0" class="buildstable">
            <div py:strip="True" py:for="rowNumber, build in enumerate(builds)">
                ${buildsTableRow(build, rowNumber, basePath, allowDelete=allowDelete, release=publishedReleases.get(build.pubReleaseId))}
            </div>
        </table>
    </div>

    <div class="pageSection" py:def="buildsTable(builds, publishedReleases=None, allowDelete=True)">
        <?python publishedReleases = publishedReleases or dict() ?>
        <form py:if="allowDelete" method="post" action="deleteBuilds">
            ${_buildsTable(builds, publishedReleases, basePath, allowDelete)}
            <p><button id="deleteBuildsSubmit" type="submit">Delete Selected Images</button></p>
        </form>
        <div py:if="not allowDelete" py:strip="True">
            ${_buildsTable(builds, publishedReleases, basePath, allowDelete)}
        </div>
    </div>

</html>
