<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
from mint.helperfuncs import truncateForDisplay
?>
    <div id="fileList" py:def="fileList(fList)">
        <table style="width: 100%;">
            <tr py:for="pathId, path, fileId, version, fObj in fList">
                <?python
                    from conary.lib import sha1helper
                    from urllib import quote
                    from conary import files
                    import os
                    from mint.helperfuncs import truncateForDisplay

                    url = "getFile?path=%s;pathId=%s;fileId=%s;fileV=%s" % (os.path.basename(path),
                                                                            sha1helper.md5ToString(pathId),
                                                                            sha1helper.sha1ToString(fileId),
                                                                            quote(version.asString()))
                ?>
                <td>${fObj.modeString()}</td>
                <td>${fObj.inode.owner()}</td>
                <td>${fObj.inode.group()}</td>
                <td>${fObj.sizeString()}</td>
                <td>${fObj.timeString()}</td>
                <td>
                    <a py:if="isinstance(fObj, files.RegularFile) and not isinstance(fObj, files.SymbolicLink)" href="${url}" title="${path}">${truncateForDisplay(path, maxWordLen = 70)}</a>
                    <span py:if="isinstance(fObj, files.SymbolicLink)">${path} -&gt; ${fObj.target()}</span>
                    <span py:if="not isinstance(fObj, files.SymbolicLink) and not isinstance(fObj, files.RegularFile)" title="${path}">${truncateForDisplay(path, maxWordLen = 70)}</span>
                </td>
            </tr>
        </table>
    </div>

    <head>
        <title>${formatTitle('Files: %s'% troveName)}</title>
    </head>
    <body>
        <div id="layout">
            <h2>Files in <a href="troveInfo?t=${troveName}" title="${troveName}">${truncateForDisplay(troveName, maxWordLen=80)}</a></h2>

            ${fileList(fileIters)}
            <hr/>
        </div>
    </body>
</html>
