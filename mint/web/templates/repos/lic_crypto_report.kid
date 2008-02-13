<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2007 rPath, Inc.
#
from mint.helperfuncs import truncateForDisplay, splitVersionForDisplay
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
    <head>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/repobrowser.js?v=${cacheFakeoutVersion}" />

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
                <th>Version</th>
                <th>Licenses</th>
                <th>Crypto</th>
            </thead>
            <tbody>
            <?python rowClass = True ?>
            <tr class="${rowClass and 'odd' or 'even'}" py:for="name, version, flavor, licenses, crypto in troves">
                <?python #
                    from mint.client import flavorWrap
                    from urllib import quote
                    url = "troveInfo?t=%s;v=%s" % (quote(name), quote(version.freeze()), quote(flavor.freeze()))
                ?>
                <td style="width: 1%; padding-right: 10px;"><a href="${url}">${name}</a></td>
                <td style="width: 33%;"><span class="expand" id="${url}_short" onclick="swapDisplay('${url}_short', '${url}_long');">${"%s:%s/%s" % (version.trailingLabel().getNamespace(), version.trailingLabel().getLabel(), version.trailingRevision().getVersion())}</span>
                <span id="${url}_long" class="collapse"  style="display: none;" onclick="swapDisplay('${url}_long', '${url}_short');">${splitVersionForDisplay(str(version))}</span></td>
                <td style="width: 25%;">
                    <div py:strip="True" py:if="licenses">
                        <div py:for="l in licenses">${XML(l)}</div>
                    </div>
                    <div py:if="not licenses">No data</div>
                </td>
                <td style="width: 25%;">
                    <div py:strip="True" py:if="crypto">
                        <div py:for="c in crypto">${XML(c)}</div>
                    </div>
                    <div py:if="not crypto">No data</div>
                </td>
                <?python rowClass = not rowClass ?>
            </tr>
            </tbody>
        </table>
    </div>

    <head/>
    <body>
        <div id="layout">
            <h2>License and Crypto for ${troveName}</h2>
            <p class="help">Although rPath believes the information provided related to the licenses and cryptography is accurate, such information may be out of date and anyone using this software should rely only on its own review of this information.</p>

            ${troveList(troves)}
        </div>
    </body>
</html>
