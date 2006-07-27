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

                <p>Use this page to manage your rMake builds.</p>

                <p>To start, create a new rMake build using the link below<span py:if="rMakeBuilds">, or select an existing build</span>.</p>

                <a href="${basePath}newrMake"><b>Create a new rMake build</b></a>
                <h2>Current rMake build</h2>
                <p py:if="rMakeBuild">
                    All packages you select by clicking on the
                    package's "Add to ${rMakeBuild.title}" link will be added to
                    this rMake build.
                </p>

                <ul>
                    <li py:if="not rMakeBuild">
                        None
                    </li>

                    <li py:if="rMakeBuild" style="font-weight: bold;">
                        <a href="${basePath}editrMake?id=${rMakeBuild.id}">${rMakeBuild.title}</a> (${len(rMakeBuild.listTroves())} troves)
                    </li>

                </ul>

                <h2>Other rMake builds</h2>

                <?python
                    otherrMakeBuilds = [x for x in rMakeBuilds if not rMakeBuild or rMakeBuild.id != x.id]
                ?>

                <p py:if="rMakeBuild and otherrMakeBuilds">
                To stop working on the current rMake build and start using
                another, click on the one you desire.</p>
                <p py:if="not rMakeBuild and otherrMakeBuilds">
                Click on the desired rMake build to make it current.</p>
                <ul py:if="not otherrMakeBuilds">
                    <li>None</li>
                </ul>

                <ul>
                    <li py:for="rmb in otherrMakeBuilds">
                        <a href="${basePath}editrMake?id=${rmb.id}">${rmb.title}</a>
                    </li>
                </ul>
            </div>
        </div>
        <div id="layout" py:if="not supported">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="spanleft">
                <h1>rMake</h1>

                <p>rMake is a package building tool that provides a clean
                  build environment, ensuring that the same package can be
                  built consistently across different machines by strictly
                  enforcing build requirements.</p>

                <p>rMake is installed on your local system and can be used
                  from the command line. rMake functionality has also been
                  integrated into rBuilder. If you have rMake installed on
                  your local system, these features will be active in the
                  rBuilder interface.</p>

                <h3>Before using rMake in rBuilder on your single-user
                  workstation, you must do the following.</h3>

                <ul>
                    <li>Access rBuilder using a Conary-based system (rPath
                      Linux)</li>

                    <li>Install the rMake package by running the following
                      command as root: <span style='font-weight: bold;'>conary update rmake --install-label=conary.rpath.com@rpl:devel --resolve</span></li>

                    <li>Start the rMake service by running the following
                      command as root: <span style='font-weight: bold;'>/sbin/service rmake start</span></li>

                </ul>

                <p>NOTE: The rMake service must be running whenever you
                  want to use rMake.  You can either start the service
                  manually each time you need it (using the /sbin/service
                  command above), or configure rMake to start automatically
                  on reboot by running the following command as root:
                  <span style='font-weight: bold;'>/sbin/chkconfig rmake on</span></p>

                <p>After installing rMake, the rMake link in your project
                  panel will lead to the rMake main page, and you can start
                  using the integrated rMake features here in rBuilder.</p>

                <p>For additional instructions, see rPath's <a
                  href="http://wiki.conary.com/wiki/rBuilder:rMake">rMake
                  documentation for rBuilder</a>.</p>
            </div>
        </div>
    </body>
</html>
