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
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/buildtemplates.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/builddefs.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript">
            addLoadEvent(function() {
                var inputBuilds = ${buildsJson};
                for(var i in inputBuilds) {
                    var build = inputBuilds[i];
                    addExisting(i, build);
                }
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
                    <tr style="font-size: larger; font-weight: bold; color: #293D82;">
                        <td style="padding-bottom: 8px;">Build type</td>
                        <td colspan="2">Options</td>
                    </tr>

                    <div py:omit="True" py:for="i, build in enumerate(builds)">
                        <tr>
                            <td>${buildtypes.typeNames[build['type']]}</td>
                            <td><a onclick="javascript:showEdit('edit_${i}');" href="#"><b>Edit</b></a></td>
                            <td><a href="#"><b>Delete</b></a></td>
                        </tr>
                        <tr><td colspan="3"><div id="edit_${i}"/></td></tr>
                    </div>
                </table>

                <div style="padding: 1em 1em 1em 2px;">
                    <span style="font-size: larger; font-weight: bold; color: #293D82; padding-right: 1em;">Add a new build:</span> <select id="newBuildType">
                        <option py:for="buildType in visibleTypes" py:content="buildtypes.typeNames[buildType]" value="${buildType}" />
                    </select>
                    <button id="newBuildButton" onclick="javascript:addNew();">Add</button>
                </div>

                <div id="newType" />

            </div>
        </div>
    </body>
</html>
