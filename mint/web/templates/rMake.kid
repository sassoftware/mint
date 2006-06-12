<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('rMake Builder')}</title>
    </head>

    <body>
        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

            <div id="spanleft">
                <h1>rMake Builder</h1>

                <p>You can use rMake Builder to create a grouping of
                packages to be built by your local rMake Server.</p>

                <p>You can only add packages from projects you are a member of</p>

                <h2>Current rMake Build</h2>

                <ul>
                    <li py:if="not rMakeBuild">
                        You are not currently using rMake Builder.
                    </li>

                    <li py:if="rMakeBuild">
                        The following rMake build is currently being processed:
                    </li>

                    <li py:if="rMakeBuild" style="font-weight: bold;">
                        <a href="${basePath}editrMake?id=${rMakeBuild.id}">${rMakeBuild.title}</a> (${len(rMakeBuild.listTroves())} troves)
                    </li>

                    <li py:if="rMakeBuild">
                        All packages you select by clicking on the
                        package's "Add this package" link will be added to
                        this rMake Build.
                    </li>
                </ul>

                <h2>Other rMake Builds</h2>

                <p>To stop working on the current rMake Build and start using
                another, click on the desired rMake Build.</p>

                <ul>
                    <li py:for="rmb in rMakeBuilds">
                        <a href="${basePath}editrMake?id=${rmb.id}">${rmb.title} <span py:if="rMakeBuild and rMakeBuild.id == rmb.id">(currently selected)</span></a>
                    </li>
                </ul>
                <a href="${basePath}newrMake"><b>Create a new rMake Build</b></a>
            </div>
        </div>
    </body>
</html>
