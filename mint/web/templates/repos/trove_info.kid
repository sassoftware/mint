<?xml version='1.0' encoding='UTF-8'?>
<?python
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved

from urllib import quote
import time
from mint import userlevels

?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">

<?python
isOwner = (userLevel == userlevels.OWNER or auth.admin)
?>

    <div py:def="breadcrumb" py:strip="True">
        <a href="${cfg.basePath}project/${project.getHostname()}/">${project.getName()}</a>
        <a href="${basePath}browse">Repository Browser</a>
        <a href="#">${troveName}</a>
    </div>

    <table py:def="sourceTroveInfo(trove)" class="troveinfo">
        <tr><th>Trove name:</th><td>${trove.getName()}</td></tr>
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

    <span py:def="lockedAdder(trove)" style="float: right;" py:if="groupTrove">
        <a href="addTrove?id=${groupTrove.id};trove=${quote(trove.getName())};version=${quote(trove.getVersion().asString())};locked=1">
            Add this exact version <img style="border: none;" src="${cfg.staticPath}apps/mint/images/group.png" />
        </a>
    </span>
    
    <span py:def="adder(trove)" style="float: right;" py:if="groupTrove">
        <a href="addTrove?id=${groupTrove.id};trove=${quote(trove.getName())};version=${quote(trove.getVersion().asString())}">
            Add this trove <img style="border: none;" src="${cfg.staticPath}apps/mint/images/group.png" />
        </a>
    </span>


    <table py:def="binaryTroveInfo(trove)" class="troveinfo">
        <?python
            sourceVersion = trove.getVersion().getSourceVersion().freeze()
            sourceLink = "troveInfo?t=%s;v=%s" % (quote(trove.getSourceName()), quote(sourceVersion))
        ?>
        <tr><th>Trove name:</th><td>${adder(trove)} ${trove.getName()}</td></tr>
        <tr><th>Version:</th><td>${lockedAdder(trove)} ${trove.getVersion().asString()}</td></tr>
        <tr><th>Flavor:</th><td>${trove.getFlavor()}</td></tr>
        <tr><th>Built from trove:</th><td><a href="${sourceLink}">${trove.getSourceName()}</a></td></tr>
        <tr><th>Build time:</th><td>${time.ctime(trove.getBuildTime())} using Conary ${trove.getConaryVersion()}</td></tr>
        <tr><th>Provides:</th>
            <td>
                <div py:for="dep in str(trove.provides.deps).split('\n')">${dep}</div>
                <div py:if="not trove.provides.deps">
                    Trove satisfies no dependencies.
                </div>
            </td>
        </tr>
        <tr><th>Requires:</th>
            <td>
                <div py:for="dep in str(trove.requires.deps).split('\n')">${dep}</div>
                <div py:if="not trove.requires.deps">
                    Trove has no requirements.
                </div>
            </td>
        </tr>
    </table>

    <head>
        <title>${formatTitle('Trove Information: %s'%troveName)}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
                ${releasesMenu(project.getReleases(), isOwner, display="none")}
                ${commitsMenu(project.getCommits(), display="none")}
                ${browseMenu(display='none')}
                ${searchMenu(display='none')}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />repository browser<br />trove information for ${troveName}</h2>

                <div py:strip="True" py:if="troves[0].getName().endswith(':source')">
                    ${sourceTroveInfo(troves[0])}
                    <p><a href="files?t=${quote(troveName)};v=${quote(troves[0].getVersion().freeze())};f=${quote(troves[0].getFlavor().freeze())}">Show Files</a></p>
                </div>
                <div py:strip="True" py:if="not trove.getName().endswith(':source')"
                     py:for="trove in troves">
                    ${binaryTroveInfo(trove)}
                    <p><a href="files?t=${quote(troveName)};v=${quote(trove.getVersion().freeze())};f=${quote(trove.getFlavor().freeze())}">Show Files</a></p>
                </div>

                <h3>All Versions:</h3>

                <ul class="troveallversions">
                    <li py:for="ver in versionList">
                        <a href="troveInfo?t=${quote(troveName)};v=${quote(ver.freeze())}"
                           py:if="ver != reqVer">${ver.asString()}</a>
                        <span py:strip="True" py:if="ver == reqVer"><b>${ver.asString()}</b> (selected)</span>
                    </li>
                </ul>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
            <div class="pad">
                ${groupTroveBuilder()}
            </div>
        </td>

    </body>
</html>
