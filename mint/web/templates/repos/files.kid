<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
?>
    <div py:def="breadcrumb" py:strip="True">

        <a
            href="${cfg.basePath}project/${project.getHostname()}/">${project.getNameForDisplay()}</a>
        <a href="${basePath}browse">Repository Browser</a>
        <a href="${basePath}troveInfo?t=${troveName}">${troveName}</a>
        <a href="#">Files</a>
    </div>

    <div id="fileList" py:def="fileList(fList)">
        <table style="width: 100%;">
            <tr py:for="pathId, path, fileId, version, fObj in fList">
                <?python
                    from conary.lib import sha1helper
                    from urllib import quote
                    from conary import files
                    import os

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
                    <a py:if="not isinstance(fObj, files.SymbolicLink)" href="${url}">${path}</a>
                    <span py:if="isinstance(fObj, files.SymbolicLink)">${path} -&gt; ${fObj.target()}</span>
                </td>
            </tr>
        </table>
    </div>

    <head>
        <title>${formatTitle('Files: %s'% troveName)}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
                <h2>Files in <a href="troveInfo?t=${troveName}">${troveName}</a></h2>

                ${fileList(fileIters)}
                <hr/>
            </div>
        </td>
    </body>
</html>
