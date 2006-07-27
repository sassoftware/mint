<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('rMake')}</title>
    </head>

    <body>
        <div id="layout" py:if="supported">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

            <div id="spanleft">
                <h1>rMake</h1>

                <p>You can use rMake to create a grouping of
                packages to be built by your local rMake Server.</p>

                <p>You can only add packages from projects you are a member of.</p>

                <h2>Current rMake build</h2>

                <ul>
                    <li py:if="not rMakeBuild">
                        You are not currently using rMake.
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
                        this rMake build.
                    </li>
                </ul>

                <h2>Other rMake builds</h2>

                <p>To stop working on the current rMake build and start using
                another, click on the desired rMake build.</p>

                <ul>
                    <li py:for="rmb in rMakeBuilds">
                        <a href="${basePath}editrMake?id=${rmb.id}">${rmb.title} <span py:if="rMakeBuild and rMakeBuild.id == rmb.id">(currently selected)</span></a>
                    </li>
                </ul>
                <a href="${basePath}newrMake"><b>Create a new rMake build</b></a>
            </div>
        </div>
        <div id="layout" py:if="not supported">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="spanleft">
                <h1>rMake</h1>

                <p>rMake is a package building tool that provides a clean build environment, ensuring that the same package can be built consistently across different machines by enforcing strict build requirements. This option is typically used to merge packages which naturally depend upon each other.</p>

                <p>rMake is a tool for use on your local system that can be used at a command line. rMake functionality has been integrated into rBuilder. If you have rMake installed on your local system, these features will be active in the rBuilder interface.</p>

                <h3>Before using rMake in rBuilder, you must do the following.</h3>

                <ul>
                    <li>Access rBuilder from a Conary-based system (rPath Linux)</li>
                    <li>Installation of the rMake package from rpath.com, which can be done by running the following update command as root: <span style='font-weight: bold;'>conary update rmake=conary.rpath.com@rpl:devel</span></li>
                    <li>Start the rMake service, which can be done by running the following command: <span style='font-weight: bold;'>/sbin/service rmake start</span></li>
                </ul>

                <p>After you successfully add rMake to your local system, the rMake link in your project panel will lead to the rMake main page, and you can start using the integrated rMake features here in rBuilder.</p>

                <p>Note that your local system will be used for all rMake processing until the new package is commited to the rBuilder repositories.</p>

                <p>For additional instructions, see rPath's <a href="http://wiki.conary.com/wiki/rBuilder:rMake">rMake documentation for rBuilder</a>.</p>
            </div>
        </div>
    </body>
</html>
