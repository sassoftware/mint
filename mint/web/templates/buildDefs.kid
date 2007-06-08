<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>Project Build Definitions</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/json.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/buildtemplates.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/builddefs.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript">
            ProjectId = ${project.id};
            LabelStr = "${label}";
            addLoadEvent(function() {
                var inputBuilds = ${buildsJson};
                for(i in inputBuilds) {
                    if(inputBuilds.hasOwnProperty(i)) {
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
            from mint.data import *
            from mint import buildtypes
        ?>
        <div id="layout">
            <div id="spanboth">

                <h2>Default Builds for ${label}</h2>

                <table>
                    <thead>
                        <tr style="font-size: larger; font-weight: bold; color: #293D82;">
                            <td style="padding-bottom: 8px;">Build type</td>
                            <td colspan="2">Options</td>
                        </tr>
                    </thead>

                    <tbody id="buildRowsBody" />
                </table>

                <div style="padding: 1em 1em 1em 2px;">
                    <span style="font-size: larger; font-weight: bold; color: #293D82; padding-right: 1em;">Add a new build:</span> <select id="newBuildType">
                        <option py:for="buildType in visibleTypes" py:content="buildtypes.typeNames[buildType]" value="${buildType}" />
                    </select>
                    <button id="newBuildButton" onclick="javascript:addNew();">Add</button>
                </div>


                <button onclick="javascript:saveChanges();" id="saveChangesButton">
                    <img id="saveChangesSpinner" class="invisible"
                        src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />
                    Save All Changes
                </button>
                <button onclick="javascript:buildAll();" id="buildAllButton">
                    <img id="buildAllSpinner" class="invisible"
                        src="${cfg.staticPath}apps/mint/images/circle-ball-dark-antialiased.gif" />
                    Build All
                </button>
                <span id="alert" />

                <p><a href="builds"><img src="${cfg.staticPath}apps/mint/images/prev.gif" /><b>Return to Builds</b></a></p>
            </div>
        </div>
    </body>
</html>
