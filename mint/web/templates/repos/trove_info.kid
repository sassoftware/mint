<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved

import time
from urllib import quote
from mint import userlevels
from mint.helperfuncs import splitVersionForDisplay, truncateForDisplay
from mint.web.templatesupport import isrMakeLegal, isGroupBuilderLegal
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">

<?python
isOwner = (userLevel == userlevels.OWNER or auth.admin)
referer = quote(req.unparsed_uri)

if troveName.startswith("group-"):
    title = "Group"
elif ":" in troveName:
    title = "Component"
else:
    title = "Package"

?>

    <table py:def="sourceTroveInfo(trove)" class="troveinfo">
        <?python
            quotedLabel = quote(str(trove.getVersion().branch().label()))
            quotedVersion = quote(trove.getVersion().asString())
            frozenVersion = quote(trove.getVersion().freeze())
            frozenFlavor = quote(trove.getFlavor().freeze())
        ?>
        <tr>
            <th>Package name:</th>
                <td title="${trove.getName()}">
                    <a py:if="isrMakeLegal(rMakeBuild, userLevel, trove.getName())"
                       style="float: right;" title="Add to ${rMakeBuild.title}"
                        href="${cfg.basePath}addrMakeTrove?trvName=${quote(trove.getName().replace(':source', ''))};label=$quotedLabel;referer=$referer">
                            Add to ${truncateForDisplay(rMakeBuild.title, maxWordLen = 10)}
                    </a>
                    ${truncateForDisplay(trove.getName(), maxWordLen=45)}
                </td>
        </tr>
        ${referencesLink("Package", trove.getName(), trove.getVersion())}
        <tr><th>Change log:</th>
            <td>
                <?python
                    cl = trove.getChangeLog()
                    timestamp = time.ctime(trove.getVersion().timeStamps()[-1])
                ?>
                <div><i>${timestamp}</i> by <i>${cl.getName()} (${cl.getContact()})</i></div>
                <p><code>${cl.getMessage()}</code></p>
            </td>
        </tr>
    </table>

    <span py:def="lockedAdder(trove, quotedVersion, referer)" style="float: right;" py:if="isGroupBuilderLegal(groupTrove, trove)">
        <a href="${groupProject.getUrl()}addGroupTrove?id=${groupTrove.id};trove=${quote(trove.getName())};version=$quotedVersion;versionLock=1;referer=$referer"
           title="Add this exact version to ${groupTrove.recipeName}">
            Add this exact version to ${truncateForDisplay(groupTrove.recipeName, maxWordLen = 10)}
        </a>
    </span>

    <span py:def="adder(trove, quotedVersion, quotedLabel, referer)" style="float: right;"
          py:if="isGroupBuilderLegal(groupTrove, trove) or isrMakeLegal(rMakeBuild, userLevel, trove.getName())">
        <a py:if="isGroupBuilderLegal(groupTrove, trove)"
           title="Add to ${groupTrove.recipeName}"
           href="${groupProject.getUrl()}addGroupTrove?id=${groupTrove.id};trove=${quote(trove.getName())};version=$quotedVersion;referer=$referer">
            Add to ${truncateForDisplay(groupTrove.recipeName, maxWordLen = 10)}
        </a>
        <a py:if="isrMakeLegal(rMakeBuild, userLevel, trove.getName())"
           title="Add to ${rMakeBuild.title}"
           href="${cfg.basePath}addrMakeTrove?trvName=${quote(trove.getName())};label=$quotedLabel;referer=$referer">
            Add to ${truncateForDisplay(rMakeBuild.title, maxWordLen = 10)}
        </a>
    </span>

    <tr py:def="referencesLink(title, n, v)" py:if="auth.authorized and cfg.allowTroveRefSearch">
        <th>Find references</th>
        <td>
            <a href="http://${SITE}findRefs?trvName=${quote(n)};trvVersion=${quote(str(v))}">
                <b><u>Search</u></b>
            </a>
            <p class="help">Search for packages which are derived from this ${title.lower()} and
                groups which include this ${title.lower()}.
            </p>
        </td>
    </tr>

    <table py:def="binaryTroveInfo(troves, title)" class="troveinfo">
        <?python
            from mint.client import flavorWrap
            trove = troves[0]
            sourceVersion = str(trove.getVersion().getSourceVersion())
            sourceLink = "troveInfo?t=%s;v=%s" % (quote(trove.getSourceName()), quote(sourceVersion))

            quotedVersion = quote(trove.getVersion().asString())
            quotedLabel = quote(trove.getVersion().branch().label().asString())
            frozenVersion = quote(trove.getVersion().freeze())
            frozenFlavor = quote(trove.getFlavor().freeze())
        ?>
        <tr>
            <th>$title name:</th>
            <td title="${trove.getName()}">${adder(trove, quotedVersion, quotedLabel, quote(req.unparsed_uri))} ${truncateForDisplay(trove.getName(), maxWordLen = 40)}</td>
        </tr>
        <tr>
            <th>Built from source:</th>
            <td><a href="${sourceLink}" title="${trove.getSourceName()}">
                ${truncateForDisplay(trove.getSourceName(), maxWordLen = 45)}
            </a></td>
        </tr>
        ${referencesLink(title, trove.getName(), trove.getVersion())}
        <tr>
            <th>Version:</th>
            <td>${lockedAdder(trove, quotedVersion, quote(req.unparsed_uri))} ${splitVersionForDisplay(str(trove.getVersion()))}</td>
        </tr>
        <tr>
            <th>Flavor:</th>
            <td>
                <div py:for="trove in troves" py:strip="True">
                    <p>${flavorWrap(trove.getFlavor())}</p>
                    <a href="#" onclick="javascript:toggle_display('${trove.getFlavor().freeze()}_items'); return false;"
                        style="text-decoration: none; vertical-align: middle;">
                        <img id="${trove.getFlavor().freeze()}_items_expander" style="vertical-align: middle;" 
                             src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /> <b><u>Details</u></b>
                    </a>
                    <table>
                        <tbody style="display: none;" id="${trove.getFlavor().freeze()}_items">
                            <tr>
                                <th>Build time: </th>
                                <td>${time.ctime(trove.getBuildTime())} using Conary ${trove.getConaryVersion()}</td>
                            </tr>
                            <tr>
                                <th>Provides: </th>
                                <td>
                                    <div py:for="dep in str(trove.provides.deps).split('\n')" title="${dep}">
                                        ${truncateForDisplay(dep, maxWordLen = 36)}
                                    </div>
                                    <div py:if="not trove.provides.deps">
                                        $title satisfies no dependencies.
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <th>Requires: </th>
                                <td>
                                    <div py:for="dep in str(trove.requires.deps).split('\n')">${dep}</div>
                                    <div py:if="not trove.requires.deps">
                                        $title has no requirements.
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td colspan="2">
                                    <a style="font-weight: bold; text-decoration: underline;"
                                       href="files?t=${quote(troveName)};v=$frozenVersion;f=$frozenFlavor">Show Contents</a>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </td>
        </tr>
    </table>

    <head>
        <title>${formatTitle('%s Information: %s' % (title, truncateForDisplay(troveName, maxWordLen = 64)))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <h2 title="${troveName}">${project.getNameForDisplay(maxWordLen = 50)} - Repository Browser</h2>
                <h3>Information for ${title.lower()}: ${truncateForDisplay(troveName, maxWordLen = 45)}</h3>

                <div py:strip="True" py:if="troves[0].getName().endswith(':source')">
                    ${sourceTroveInfo(troves[0])}
                    <p><a href="files?t=${quote(troveName)};v=${quote(troves[0].getVersion().freeze())};f=${quote(troves[0].getFlavor().freeze())}">Show Files</a></p>
                </div>
                <div py:strip="True" py:if="not troves[0].getName().endswith(':source')">
                    ${binaryTroveInfo(troves, title)}
                </div>

                <h3>All Versions:</h3>

                <ul class="troveallversions">
                    <li py:for="ver in versionList">
                        <a href="troveInfo?t=${quote(troveName)};v=${quote(ver.freeze())}"
                           py:if="ver != reqVer">${splitVersionForDisplay(str(ver))}</a>
                        <span py:strip="True" py:if="ver == reqVer"><b>${splitVersionForDisplay(str(ver))}</b> (selected)</span>
                    </li>
                </ul>
            </div>
        </div>
    </body>
</html>
