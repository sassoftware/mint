<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Group Builder: %s' % project.getNameForDisplay())}</title>
        <script>
            function allowXen() {
                buildArch = $('buildArch');
                if(buildArch.selectedIndex != 0) {
                    $('domU').disabled = true;
                    $('domU').checked = false;
                    setOpacity($('domULabel'), 0.5);
                } else {
                    $('domU').disabled = false;
                    setOpacity($('domULabel'), 1);
                }
            }
        </script>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="right" class="side">
                ${projectsPane()}
            </div>
            <div id="middle">
                <h1 id="pleaseWait">Cooking Group: Choose An Architecture</h1>

                <p>You can choose an architecture to cook this group for. If you want your application image to support
                more than one architecture, cook the group once for each you wish to support.</p>

                <form method="post" action="cookGroup">
                    <p>
                        <select name="flavor" id="buildArch" onchange="allowXen();">
                            <option value="1#x86">x86 (32-bit)</option>
                            <option value="1#x86_64">x86_64 (64-bit)</option>
                        </select>

                    </p>
                    <p>
                        You can optionally add Xen guest domain (domU) support to this group.
                    </p>
                    <p>
                        <div>
                            <input name="flavor" type="checkbox" value="5#use:domU:xen" id="domU" />
                            <label id="domULabel" for="domU">Xen domU (unprivileged guest) support</label>
                        </div>
                    </p>
                    <p><button class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/cook_button.png" alt="Cook Group" /></button></p>
                    <input type="hidden" name="id" value="${groupTroveId}" />
                </form> 
            </div>
        </div>
    </body>
</html>
