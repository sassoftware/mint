<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2006 rPath, Inc.
#
from mint.helperfuncs import truncateForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
    <div id="fileList" py:def="troveList(troves)">
        <table style="width: 100%;">
            <tr py:for="name, version, flavor in troves">
                <?python #
                    from mint.client import flavorWrap
                    from urllib import quote
                    url = "files?t=%s;v=%s;f=%s" % (quote(name), quote(version.freeze()), quote(flavor.freeze()))
                ?>
                <td style="width: 25%;"><a href="${url}">${name}</a></td>
                <td style="width: 25%;">${str(version)}</td>
                <td style="width: 50%;">${flavorWrap(flavor)}</td>
            </tr>
        </table>
    </div>

    <head/>
    <body>
        <div id="layout">
            <h2>Troves in <a href="troveInfo?t=${troveName}" title="${troveName}">${truncateForDisplay(troveName, maxWordLen=80)}</a></h2>

            ${troveList(troves)}
        </div>
    </body>
</html>
