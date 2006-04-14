<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved

from urllib import quote
import time
from mint import userlevels
from mint.helperfuncs import splitVersionForDisplay, truncateForDisplay

?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">

<?python
isOwner = (userLevel == userlevels.OWNER or auth.admin)
?>

    <table py:def="sourceTroveInfo(trove)" class="troveinfo">
        <tr><th>Trove name:</th><td title="${trove.getName()}">${truncateForDisplay(trove.getName(), maxWordLen=45)}</td></tr>
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

    <span py:def="lockedAdder(trove)" style="float: right;" py:if="groupTrove and not groupTrove.troveInGroup(trove.getName())">
        <a href="${groupProject.getUrl()}addGroupTrove?id=${groupTrove.id};trove=${quote(trove.getName())};version=${quote(trove.getVersion().asString())};versionLock=1;referer=${quote(req.unparsed_uri)}" title="Add this exact version to ${groupTrove.recipeName}">
            Add this exact version to ${truncateForDisplay(groupTrove.recipeName, maxWordLen = 10)}
        </a>
    </span>

    <span py:def="adder(trove)" style="float: right;"
        py:if="groupTrove and not groupTrove.troveInGroup(trove.getName())">
        <a href="${groupProject.getUrl()}addGroupTrove?id=${groupTrove.id};trove=${quote(trove.getName())};version=${quote(trove.getVersion().asString())};referer=${quote(req.unparsed_uri)}" title="Add to ${groupTrove.recipeName}">
            Add to ${truncateForDisplay(groupTrove.recipeName, maxWordLen = 10)}
        </a>
    </span>


    <table py:def="binaryTroveInfo(troves)" class="troveinfo">
        <?python
            from mint.mint import flavorWrap
            trove = troves[0]
            sourceVersion = trove.getVersion().getSourceVersion().freeze()
            sourceLink = "troveInfo?t=%s;v=%s" % (quote(trove.getSourceName()), quote(sourceVersion))
        ?>
        <tr><th>Trove name:</th><td title="${trove.getName()}">${adder(trove)} ${truncateForDisplay(trove.getName(), maxWordLen = 40)}</td></tr>
        <tr><th>Built from trove:</th><td><a href="${sourceLink}" title="${trove.getSourceName()}">${truncateForDisplay(trove.getSourceName(), maxWordLen = 45)}</a></td></tr>
        <tr><th>Version:</th><td>${lockedAdder(trove)} ${splitVersionForDisplay(str(trove.getVersion()))}</td></tr>
        <tr><th>Flavor:</th><td>
	<div py:for="trove in troves" py:strip="True">
	    <p>${flavorWrap(trove.getFlavor())}</p>
            <a href="#" onclick="javascript:toggle_display('${trove.getFlavor().freeze()}_items'); return false;">Details <img id="${trove.getFlavor().freeze()}_items_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></a>
	    <table>
		<tbody style="display: none;" id="${trove.getFlavor().freeze()}_items">
		    <tr><th>Build time: </th><td>${time.ctime(trove.getBuildTime())} using Conary ${trove.getConaryVersion()}</td></tr>
		    <tr>
			<th>Provides: </th>
			<td>
			    <div py:for="dep in str(trove.provides.deps).split('\n')" title="${dep}">${truncateForDisplay(dep, maxWordLen = 36)}</div>
			    <div py:if="not trove.provides.deps">
				Trove satisfies no dependencies.
			    </div>
			</td>
		    </tr>
		    <tr>
			<th>Requires: </th>
			<td>
			    <div py:for="dep in str(trove.requires.deps).split('\n')">${dep}</div>
			    <div py:if="not trove.requires.deps">
				Trove has no requirements.
			    </div>
			</td>
		    </tr>
		    <tr><td colspan="2"><a href="files?t=${quote(troveName)};v=${quote(trove.getVersion().freeze())};f=${quote(trove.getFlavor().freeze())}">Show Troves</a></td></tr>
		</tbody>
	    </table>
        </div></td></tr>
    </table>

    <head>
        <title>${formatTitle('Trove Information: %s' % truncateForDisplay(troveName, maxWordLen = 64))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(project.getReleases(), isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${groupTroveBuilder()}
            </div>
            <div id="middle">
                <h2 title="${troveName}">${project.getNameForDisplay(maxWordLen = 50)}<br />Repository Browser<br />Trove information for ${truncateForDisplay(troveName, maxWordLen = 45)}</h2>

                <div py:strip="True" py:if="troves[0].getName().endswith(':source')">
                    ${sourceTroveInfo(troves[0])}
                    <p><a href="files?t=${quote(troveName)};v=${quote(troves[0].getVersion().freeze())};f=${quote(troves[0].getFlavor().freeze())}">Show Files</a></p>
                </div>
                <div py:strip="True" py:if="not troves[0].getName().endswith(':source')">
                    ${binaryTroveInfo(troves)}
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
