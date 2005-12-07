<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005 rPath, Inc.
#
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
    <div id="fileList" py:def="troveList(troves)">
        <table style="width: 100%;">
            <tr py:for="name, version, flavor in troves">
                <?python #
                    from mint.mint import flavorWrap
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
        <td id="main" class="spanall">
            <div class="pad">
                <h2>Troves in <a href="troveInfo?t=${troveName}">${troveName}</a></h2>

                ${troveList(troves)}
            </div>
        </td>
    </body>
</html>
