<?xml version='1.0' encoding='UTF-8'?>
<?python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
from mint.helperfuncs import truncateForDisplay, splitVersionForDisplay
from mint.web.templatesupport import projectText
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
                <th>${projectText().title()}</th>
            </thead>
            <tbody>
            <tr py:for="name, version, flavor in troves">
                <?python #
                    from mint.client import flavorWrap
                    from urllib import quote
                    url = "files?t=%s;v=%s;f=%s" % (quote(name), quote(version.freeze()), quote(flavor.freeze()))
                ?>
                <td style="width: 32%;"><a href="${url}">${name}</a></td>
                <td style="width: 32%;"><span class="expand" id="${url}_short" onclick="swapDisplay('${url}_short', '${url}_long');">${"%s:%s/%s" % (version.trailingLabel().getNamespace(), version.trailingLabel().getLabel(), version.trailingRevision().getVersion())}</span>
                <span id="${url}_long" class="collapse"  style="display: none;" onclick="swapDisplay('${url}_long', '${url}_short');">${splitVersionForDisplay(str(version))}</span></td>
                <td style="width: 32%;">${"%s" % version.trailingLabel().getHost()}</td>
            </tr>
            </tbody>
        </table>
    </div>
    
    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div class="full-content">
                <div class="page-title-no-project">Troves in <a href="troveInfo?t=${troveName}" title="${troveName}">${truncateForDisplay(troveName, maxWordLen=80)}</a></div>
               
                <p class="help">The following troves are included in ${troveName}.  Click <a href="javascript:history.back();">Back</a> to return to the repository browser.</p>

                ${troveList(troves)}
            </div>
            <br class="clear"/>
            <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
