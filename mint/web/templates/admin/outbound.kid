<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Outbound Mirroring')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/removeOutbound" method="post">
                <h2>Outbound Mirrored Projects</h2>
                <p class="help">
                    You can select projects in ${cfg.productName} to be mirrored out to
                    an external Conary repository.
                </p>

                <table cellspacing="0" cellpadding="0" class="results">
                    ${columnTitles(columns)}
                    ${searchResults(rows)}
                </table>
                <button py:if="rows" style="float: right;" type="submit" name="operation" value="remove_outbound">Remove Selected</button>
            </form>
            <p style="clear: right;"><b><a href="${cfg.basePath}admin/addOutbound">Add an Outbound Mirror</a></b></p>
        </div>
    </body>
</html>
