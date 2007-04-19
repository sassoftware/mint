<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
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
                    import urllib
                    from conary import versions

                    url = "getFile?path=%s;pathId=%s;fileId=%s;fileV=%s" % (os.path.basename(path),
                                                                            sha1helper.md5ToString(pathId),
                                                                            sha1helper.sha1ToString(fileId),
                                                                            quote(version.asString()))
                    troveVersion = None
                    if version.isModifiedShadow():
                        attrs = urllib.splitattr(self.toUrl)[1]
                        for x in attrs:
                            param, value = urllib.splitvalue(x)
                            if param == 'v':
                                troveVersion = versions.ThawVersion(urllib.unquote(value)).branch().asString()
                                break
                    from conary import checkin
                    if checkin.nonCfgRe.match(os.path.basename(path)):
                        binFile = True
                    else:
                        binFile = False
                ?>
                <td py:attrs="{'class': version.branch().asString() == troveVersion and 'modified' or None }">${fObj.modeString()}</td>
                <td py:attrs="{'class': version.branch().asString() == troveVersion and 'modified' or None }" >${fObj.inode.owner()}</td>
                <td py:attrs="{'class': version.branch().asString() == troveVersion and 'modified' or None }">${fObj.inode.group()}</td>
                <td py:attrs="{'class': version.branch().asString() == troveVersion and 'modified'  or None}">${fObj.sizeString()}</td>
                <td py:attrs="{'class': version.branch().asString() == troveVersion and 'modified' or None }">${fObj.timeString()}</td>
                <td style="width: auto;" py:attrs="{'class': version.branch().asString() == troveVersion and 'modified' or None }">
                    <a py:if="isinstance(fObj, files.RegularFile) and not isinstance(fObj, files.SymbolicLink)" href="${url}" title="${path}">${truncateForDisplay(path, maxWordLen = 70)}</a>
                    <span py:if="isinstance(fObj, files.SymbolicLink)">${path} -&gt; ${fObj.target()}</span>
                    <span py:if="not isinstance(fObj, files.SymbolicLink) and not isinstance(fObj, files.RegularFile)" title="${path}">${truncateForDisplay(path, maxWordLen = 70)}</span>
                </td>
                <td py:if="troveName.endswith(':source')">
                    <a py:if="version.branch().asString() == troveVersion and not binFile " href="${'diffShadow?t=%s;v=%s;path=%s;pathId=%s;fileId=%s' % (troveName, quote(version.asString()), os.path.basename(path), sha1helper.md5ToString(pathId), sha1helper.sha1ToString(fileId))}"><button>Calculate Diff</button></a>
                </td>
            </tr>
                <tr  py:if="deletedFiles" py:for="pathId, path, fileId, version, fObj in deletedFiles">
                        <td style="text-decoration: line-through;">${fObj.modeString()}</td>
                        <td style="text-decoration: line-through;">${fObj.inode.owner()}</td>
                        <td  style="text-decoration: line-through;">${fObj.inode.group()}</td>
                        <td  style="text-decoration: line-through;">${fObj.sizeString()}</td>
                        <td  style="text-decoration: line-through;">${fObj.timeString()}</td>
                        <td  style="text-decoration: line-through;">${truncateForDisplay(path, maxWordLen = 70)}</td>
                    </tr>
        </table>
    </div>

    <head>
        <title>${formatTitle('Files: %s'% troveName)}</title>
    </head>
    <body>
        <div id="layout">
            <h2>Files in <a href="troveInfo?t=${troveName}" title="${troveName}">${truncateForDisplay(troveName, maxWordLen=80)}</a></h2>
            <p class="help">Shadowed files that have been modified on the current branch are displayed in <span class="modified">blue</span>.</p>
            <p py:if="deletedFiles" class="help">Shadowed files that have been deleted on the current branch are displayed in <span style="text-decoration: line-through;">strike-through</span>.</p>

            ${fileList(fileIters)}
            <hr/>
        </div>
    </body>
</html>
