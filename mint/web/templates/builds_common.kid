<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
# All Rights Reserved
#
from mint.web.templatesupport import downloadTracker, projectText
from mint.helperfuncs import truncateForDisplay, formatProductVersion
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
    <div py:strip="True" py:def="buildsTableRow(build, rowNumber, basePath, allowDelete)">
        <?python
            from mint import buildtypes
            from mint.helperfuncs import truncateForDisplay
            rowAttrs = { 'class': (rowNumber % 2) and 'odd' or 'even' }
            isPublished = build.getPublished()
        ?>
        <tr py:attrs="rowAttrs">
            <td colspan="3" class="buildName"><a href="${basePath}build?id=${build.id}">${truncateForDisplay(build.name)}</a>
                <span py:if="isPublished" class="buildAssociated">
                    <?python
                        release = self.client.getPublishedRelease(build.pubReleaseId)
                    ?>
                    <br />Part of ${isPublished and 'published' or 'unpublished'} release <a href="${basePath}release?id=${release.id}">${release.name} (Version ${release.version}) </a></span>
            </td>
        </tr>
        <tr py:attrs="rowAttrs">
            <td class="buildInfo">${build.getTroveName()}<br />${"%s/%s" % (build.getTroveVersion().trailingLabel(), build.getTroveVersion().trailingRevision())}</td>
            <td py:if="build.getBuildType() != buildtypes.IMAGELESS" class="buildInfo">${build.getArch()}&nbsp;${buildtypes.typeNamesShort.get(build.getBuildType(), 'Unknown')}</td>
            <td py:if="build.getBuildType() == buildtypes.IMAGELESS" class="buildInfo">&nbsp;${buildtypes.typeNamesShort.get(build.getBuildType(), 'Unknown')}</td>
            <td class="buildInfo">&nbsp;<input py:if="not isPublished and allowDelete" style="float: right;" name="buildIdsToDelete" type="checkbox" value="${build.id}" />
            </td>
        </tr>
    </div>

    <div py:strip="True" py:def="_buildsTable(builds, basePath, allowDelete)">
        <table py:if="builds" border="0" cellspacing="0" cellpadding="0" class="buildstable">
            <div py:strip="True" py:for="rowNumber, build in enumerate(builds)">
                ${buildsTableRow(build, rowNumber, basePath, allowDelete=allowDelete)}
            </div>
        </table>
    </div>

    <div py:strip="True" py:def="buildsTable(builds, allowDelete=True)">
        <form py:if="allowDelete" method="post" action="deleteBuilds">
            ${_buildsTable(builds, basePath, allowDelete)}
            <p><button id="deleteBuildsSubmit" type="submit">Delete Selected Images</button></p>
        </form>
        <div py:if="not allowDelete" py:strip="True">
            ${_buildsTable(builds, basePath, allowDelete)}
        </div>
    </div>

</html>
