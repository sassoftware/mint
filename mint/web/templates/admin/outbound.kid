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
                    an external Conary repository or Update Service.
                </p>

                <table py:if="rows" cellspacing="0" cellpadding="0" class="results">
                    <tr>
                        <th>Project</th>
                        <th>Targets</th>
                        <th>Include Sources</th>
                        <th>Order</th>
                        <th>Remove</th>
                    </tr>
                    <div py:strip="True" py:for="data in rows">
                        <tr>
                            <td><a href="${data.get('projectUrl')}">${data.get('projectName')}</a><br /><div style="font-size: smaller;"><span py:if="data.get('group')" py:strip="True">${data.get('group')}</span><span py:if="data.get('allLabels') and not data.get('group')" py:strip="True">All Labels</span><div py:for="l in data.get('labels', [])" py:strip="True" py:if="not data.get('group')">${l}<br /></div></div></td>
                            <td style="font-size: smaller;"><div py:if="not data.get('targets', [])" style="color: red;">No targets defined</div><div py:for="tId, tUrl in data.get('targets', [])">${tUrl} <a href="removeOutboundMirrorTarget?id=${tId}">(delete)</a><br /></div><a href="addOutboundMirrorTarget?id=${data.get('id')}">Add target...</a></td>
                            <td py:content="data.get('mirrorSources') and 'Yes' or 'No'" />
                            <td py:content="data.get('orderHTML')" />
                            <td><input type="checkbox" name="remove" value="${data.get('id')}" /></td>
                        </tr>
                    </div>

                </table>
                <button py:if="rows" style="float: right;" type="submit" name="operation" value="remove_outbound">Remove Selected</button>
            </form>
            <p style="clear: right;"><b><a href="${cfg.basePath}admin/addOutbound">Add an Outbound Mirror</a></b></p>
        </div>
    </body>
</html>
