<?xml version='1.0' encoding='UTF-8'?>
<?python
import re
from mint.mint import extractIs
from mint.releasedata import RDT_STRING, RDT_BOOL, RDT_INT
title = "Edit Release"

def generateJs(archMap):
    arches = sorted(archMap.keys())
    js = "versionFlavors = Array(%d);\n" % len(arches)
    
    for i, arch in enumerate(arches):
        js += "versionFlavors[%d] = Array(" % i
        js += ", ".join("Array('%s', '%s', '%s')" % (x[0].asString(),
                                                     x[0].freeze(),
                                                     x[1].freeze()) for x in archMap[arch])
        js += ");\n";
    return js
?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="${basePath}releases">Releases</a>
        <a href="#">Edit Release</a>
    </div>

    <head>
        <title>${formatTitle('Edit Release')}</title>
    </head>
    <body onload="javascript:pickArch(); pickVersion();">
    <script>
        ${generateJs(archMap)}
    <![CDATA[
        function pickArch()
        {
            arch = document.getElementById("arch")
            sel = document.getElementById("versions");
            clearSelection(sel);

            vfs = versionFlavors[arch.selectedIndex];
            for(var i=0; i < vfs.length; i++) {
                appendToSelect(sel, vfs[i][1] + ' ' + vfs[i][2], document.createTextNode(vfs[i][0]), "version");
            }
            for(var i=0; i < sel.options.length; i++)
                if(vfs[i][1] == '${version and version.freeze() or ''}')
                    sel.selectedIndex = i
        }

        function pickVersion() 
        {
            arch = document.getElementById("arch").selectedIndex;
            sel = document.getElementById("versions").selectedIndex;
        }
    ]]>
    </script>
    <td id="left" class="side">
        <div class="pad">
            ${projectResourcesMenu()}
        </div>
    </td>
    <td id="main">
        <div class="pad">
            <h2>Release</h2>
            <form method="post" action="editRelease2">
                <table cellpadding="6">
                    <tr><td>Trove:</td><td>${trove}=${label}</td></tr>
                    <tr>
                        <td>Architecture:</td>
                        <td><select onchange="javascript:pickArch();" id="arch">
                                <option py:for="arch in sorted(archMap.keys())"
                                        py:attrs="{'selected': (flavor and arch == extractIs(flavor)) and 'selected' or None}">
                                    ${arch}
                                </option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td style="width: 20%;">Version:</td>
                        <td><select onchange="javascript:pickVersion();"
                                    name="version" id="versions"></select>
                        </td>
                    </tr>
                </table>

                <h2>Release Notes</h2>
                <p>Please provide notes for this release:</p>
                <textarea style="background-color: #eee; width: 80%; margin-left: 10px;"
                          rows="6" name="desc">${release.getDesc()}</textarea>
                
                <h2>Settings</h2>
                <table cellpadding="6" id="releaseData">
                    <?python
                        template = release.getDataTemplate()
                        dataDict = release.getDataDict()
                        
                    ?>
                    <tr py:for="name, dataRow in sorted(template.items(), key = lambda x: x[1][0])">
                        <td py:if="(dataRow[0] == RDT_BOOL) and dataDict[name]" colspan="2">
                            <input type="checkbox" name="${name}" value="1" checked="checked"/> ${dataRow[2]}
                        </td>
                        <td py:if="(dataRow[0] == RDT_BOOL) and not dataDict[name]" colspan="2">
                            <input type="checkbox" name="${name}" value="1"/> ${dataRow[2]}
                        </td>
                        <td py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)" style="width: 40%;">
                            ${dataRow[2]}
                        </td>
                        <td py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)">
                            <input class="text" type="text" name="${name}" value="${dataDict[name]}"/>
                        </td>

                    </tr>
                </table>

                <p><input type="submit" value="Save" /></p>
                <input type="hidden" name="releaseId" value="${release.getId()}"/>
                <input type="hidden" name="trove" value="${trove}"/>
            </form>

            <div py:if="0" style="text-align: right;">
                <form method="post" action="deleteRelease">
                    <input type="hidden" name="releaseId" value="${release.getId()}"/>
                    <p>FIXME: Remove an unwanted release of your distribution: <input type="submit" value="Delete Release" /></p>
                </form>
            </div>
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
