<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2007-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
from mint.web.templatesupport import projectText
?>

    <head>
        <title>${projectText().title()} Image Definitions</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/json.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/buildtemplates.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/builddefs.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript">
            ProjectId = ${project.id};
            LabelStr = "${label}";
            Flavors = {
                '32-bit (x86)': '~!domU,~!kernel.pae,~!vmware,~!xen is: x86',
                '32-bit (x86) VMware': '~!domU,!kernel.pae,vmware,~!xen is: x86',
                '32-bit (x86) DomU': 'domU,~kernel.pae,~!vmware,xen is: x86',
                '64-bit (x86-64)': '~!domU,~!vmware,~!xen is: x86_64',
                '64-bit (x86-64) VMware': '~!domU,vmware,~!xen is: x86_64',
                '64-bit (x86-64) DomU': 'domU,~!vmware,xen is: x86_64',
                'Other (enter below...)': '',
            };

            addLoadEvent(function() {
                var inputBuilds = ${buildsJson};
                $('troveName').value = inputBuilds[0]['troveName'];
                for(i in inputBuilds) {
                    if(inputBuilds.hasOwnProperty(i) &amp;&amp; i > 0) {
                        var build = inputBuilds[i];
                        addExisting(i, build);
                    }
                }
                setupRows();
            });
        </script>
    </head>

    <body>
        <?python
            from mint.lib.data import *
            from mint import buildtypes
        ?>
        <div id="layout">
            <div id="spanboth">

                <h2>Default Image Definitions for ${label}</h2>

                <p>Group name: <input type="text" id="troveName" name="troveName" /></p>

                <table>
                    <thead>
                        <tr style="font-size: larger; font-weight: bold; color: #293D82;">
                            <td style="padding-bottom: 8px;">Image type</td>
                            <td colspan="2" style="text-align: right;">Options</td>
                        </tr>
                    </thead>

                    <tbody id="buildRowsBody" />
                </table>

                <div style="padding: 1em 1em 1em 2px;">
                    <span style="float: right">
                        <button onclick="javascript:saveChanges(false);" id="saveChangesButton">
                            <img id="saveChangesSpinner" class="invisible"
                                src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />
                            Save All Changes
                        </button>
                        <button onclick="javascript:saveChanges(true);" id="buildAllButton">
                            <img id="buildAllSpinner" class="invisible"
                                src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />
                            Build All Images
                        </button>
                    </span>

                    <span style="font-size: larger; font-weight: bold;
                        color: #293D82; padding-right: 1em;">Add a new
                        image definition:</span> <select id="newBuildType">
                        <option py:for="buildType in visibleTypes" py:content="buildtypes.typeNames[buildType]" value="${buildType}" />
                    </select>
                    <button id="newBuildButton" onclick="javascript:addNew();">Add</button>
                </div>
                <div id="alert" />

                <p><a href="builds"><img src="${cfg.staticPath}apps/mint/images/prev.gif"/>
		<b>Return to image list</b></a></p>
            </div>
        </div>
    </body>
</html>
