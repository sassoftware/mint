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
from conary import deps
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

    <table py:def="sourceTroveInfo(trove, referer)" class="troveinfo">
        <?python
            quotedLabel = quote(str(trove.getVersion().branch().label()))
            quotedVersion = quote(trove.getVersion().asString())
            frozenVersion = quote(trove.getVersion().freeze())
            frozenFlavor = quote(trove.getFlavor().freeze())
            clonedFrom = trove.troveInfo.clonedFrom()
            clonedFromStr = ''
            if clonedFrom and '@LOCAL:' not in clonedFrom.asString():
                clonedLink = "troveInfo?t=%s;v=%s" % (trove.getName(), quote(clonedFrom.asString()))
                clonedFromStr = clonedFrom.asString()
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
        <tr py:if="clonedFromStr">
            <th>Cloned from:</th>
            <td><a href="${clonedLink}">${splitVersionForDisplay(clonedFromStr)}</a></td>
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
                <b><u>Search</u></b></a><p class="help" style="display: inline;"> for packages derived from this ${title.lower()} and
                groups which include this ${title.lower()}.</p>
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
            clonedFrom = trove.troveInfo.clonedFrom()
            clonedFromStr = ''
            if clonedFrom and '@LOCAL:' not in clonedFrom.asString():
                clonedLink = "troveInfo?t=%s;v=%s" % (trove.getName(), quote(clonedFrom.asString()))
                clonedFromStr = clonedFrom.asString()

            flavors = []
            for x in troves:
                flavors.append(x.getFlavor())
            reducedFlavors = deps.deps.flavorDifferences(flavors)
        ?>
        <tr>
            <th style="font-weight: bold;">$title name:</th>
            <td style="font-weight: bold;" title="${trove.getName()}">${adder(trove, quotedVersion, quotedLabel, quote(req.unparsed_uri))} ${truncateForDisplay(trove.getName(), maxWordLen = 40)}</td>
        </tr>
        <tr>
            <th>Branch and Version:</th>
            <td><a href="javascript:void(0);" id="shortVersion" onclick="hideElement(this); showElement('longVersion');">${'%s:%s' % (str(trove.getVersion().trailingLabel().getNamespace()), str(trove.getVersion().trailingLabel().getLabel()))}/${str(trove.getVersion().trailingRevision().getVersion())}</a>
            <a href="javascript:void(0);" id="longVersion" onclick="hideElement(this); showElement('shortVersion');">${splitVersionForDisplay(str(trove.getVersion()))}</a>${lockedAdder(trove, quotedVersion, quote(req.unparsed_uri))} </td>
        </tr>
        <tr>
            <th>Built from source:</th>
            <td><a href="${sourceLink}" title="${'%s=%s' %(trove.getSourceName(), trove.getVersion())}">
                ${truncateForDisplay(trove.getSourceName(), maxWordLen = 45)}
            </a></td>
        </tr>
        <tr py:if="clonedFromStr">
            <th>Cloned from:</th>
            <td><a href="${clonedLink}">${splitVersionForDisplay(clonedFromStr)}</a></td>
        </tr>
        <tr>
            <th py:if="len(troves) > 1">Flavors:</th>
            <th py:if="len(troves) == 1">&nbsp;</th>
            <td>
                <div py:for="trove in troves" py:strip="True">
                    <span py:if="len(troves) > 1">${flavorWrap(reducedFlavors[trove.getFlavor()])}</span><br/>
                     <div style="vertical-align: middle; margin-top: 10px; margin-bottom: 10px;">
                     <a style="font-weight: normal; text-decoration: underline;"
                                       href="files?t=${quote(troveName)};v=$frozenVersion;f=$frozenFlavor">Show Contents</a>
                    </div>
                    <a href="#" onclick="javascript:toggle_display('${trove.getFlavor().freeze()}_items'); return false;"
                        style="text-decoration: none; vertical-align: middle;">
                        <img id="${trove.getFlavor().freeze()}_items_expander" style="vertical-align: middle;" 
                             src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /> <u>Details</u>
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
                        </tbody>
                    </table>
                    <div py:if="len(troves) > 1" style="border-bottom:1px #e6e6e6 solid; margin-bottom: 15px; padding-bottom: 5px;" />
                </div>
            </td>
        </tr>
        ${referencesLink(title, trove.getName(), trove.getVersion())}
    </table>

    <head>
        <title>${formatTitle('%s Information: %s' % (title, truncateForDisplay(troveName, maxWordLen = 64)))}</title>
        <script type="text/javascript">
            addLoadEvent(function(){hideElement('longVersion')});
        </script>
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

                <div py:strip="True" py:if="troves[0].getName().endswith(':source')">
                    ${sourceTroveInfo(troves[0], referer)}
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
