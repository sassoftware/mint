<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('External Projects')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <h2>Externally-Managed Projects</h2>
            <p class="help">Externally-managed projects allow a remote Conary repository to be accessible by
                    this rBuilder. Click on the name of an external project to edit its settings.</p>
            <table cellspacing="0" cellpadding="0" class="results">
                ${columnTitles(regColumns)}
                ${searchResults(regRows)}
            </table>

            <h2>Mirrored Projects</h2>
            <table cellspacing="0" cellpadding="0" class="results">
                ${columnTitles(mirrorColumns)}
                ${searchResults(mirrorRows)}
            </table>

            <p><a href="addExternal"><b>Add a New External Project</b></a></p>
        </div>
    </body>
</html>
