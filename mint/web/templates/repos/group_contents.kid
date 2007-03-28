<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
#
from mint.helperfuncs import truncateForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
    <head>
        <script type="text/javascript">
            function init() {
                var elems = getElementsByTagAndClassName(null, 'versionLong');
                var i;
                for(i = 0; elems.length > i; i++) {
                    hideElement(elems[i]);
                }
            }
            addLoadEvent(init);
        </script>
    </head>
            
    <div id="fileList" py:def="troveList(troves)">
        <table style="width: 100%;">
            <thead>
                <th>Trove</th>
                <th>Branch and Version</th>
                <th>Project</th>
            </thead>
            <tbody>
            <tr py:for="name, version, flavor in troves">
                <?python #
                    from mint.client import flavorWrap
                    from urllib import quote
                    url = "files?t=%s;v=%s;f=%s" % (quote(name), quote(version.freeze()), quote(flavor.freeze()))
                ?>
                <td style="width: 32%;"><a href="${url}">${name}</a></td>
                <td style="width: 32%;"><a id="${url}_short" href="javascript:void(0);" onclick="hideElement(this); showElement('${url}_long');">${"%s:%s/%s" % (version.trailingLabel().getNamespace(), version.trailingLabel().getLabel(), version.trailingRevision().getVersion())}</a><a id="${url}_long" class="versionLong" href="javascript:void(0);" onclick="hideElement(this); showElement('${url}_short');">${str(version)}</a></td>
                <td style="width: 32%;">${"%s" % version.trailingLabel().getHost()}</td>
            </tr>
            </tbody>
        </table>
    </div>

    <head/>
    <body>
        <div id="layout">
            <h2>Troves in <a href="troveInfo?t=${troveName}" title="${troveName}">${truncateForDisplay(troveName, maxWordLen=80)}</a></h2>
            <p class="help">The following troves are included in ${troveName}.  Click <a href="javascript:history.back();">Back</a> to return to the repository browser.</p>

            ${troveList(troves)}
        </div>
    </body>
</html>
