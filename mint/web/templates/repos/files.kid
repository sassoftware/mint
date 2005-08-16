<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../library.kid', '../layout.kid'">
<!--
 Copyright (c) 2005 rpath, Inc.

 All Rights Reserved
-->

    <div py:def="breadcrumb" py:strip="True">
        <a href="/">${project.getName()}</a>
        <a href="/conary/browse">Repository Browser</a>
        <a href="/conary/troveInfo?t=${troveName}">${troveName}</a>
        <a href="#">Files</a>
    </div>

    <div id="fileList" py:def="fileList(files)">
        <table style="width: 100%;">
            <tr py:for="pathId, path, fileId, version, fObj in files">
                <?python #
                    from lib import sha1helper
                    import os
                    from urllib import quote

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
                <td><a href="${url}">${path}</a></td>
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
