<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.web.templatesupport import projectText
?>
    <head>
        <title>${formatTitle('Outbound Mirroring')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/removeOutbound" method="post">
                <h2>Outbound Mirrored ${projectText().title()}s</h2>
                <p class="help">
                    You can select ${projectText().lower()}s in ${cfg.productName} to be mirrored out to
                    an external Conary repository or Update Service.
                </p>

                <table py:if="rows" cellspacing="0" cellpadding="0" class="results">
                    <tr>
                        <th>${projectText().title()}</th>
                        <th>Targets</th>
                        <th>Include Sources</th>
                        <th>Order</th>
                        <th>Remove</th>
                    </tr>
                    <div py:strip="True" py:for="data in rows">
                        <tr>
                            <td>
                                <a href="editOutbound?id=${data.get('id')}">${data.get('projectName')}</a>
                                <br />
                                <div style="font-size: smaller;">
                                    <span py:if="data['useReleases']" py:strip="True">All releases</span>
                                    <span py:if="not data['useReleases']" py:strip="True">
                                        <span py:if="not data['groups']" py:strip="True">All packages<br /></span>
                                        <div py:for="g in data.get('groups',[])" py:strip="True">${g}<br /></div>

                                        <span py:if="data['allLabels']" py:strip="True">All labels</span>
                                        <div py:for="l in data.get('labels', [])" py:strip="True">${l}<br /></div>
                                    </span>
                                </div>
                            </td>
                            <td style="font-size: smaller;"><div py:if="not data.get('targets', [])" style="color: red;">No targets defined</div><div py:for="tId, tUrl in data.get('targets', [])">${tUrl}<br /></div></td>
                            <td py:content="data.get('mirrorSources') and 'Yes' or 'No'" />
                            <td py:content="data.get('orderHTML')" />
                            <td><input type="checkbox" name="remove" value="${data.get('id')}" /></td>
                        </tr>
                    </div>

                </table>
                <button py:if="rows" style="float: right;" type="submit" name="operation" value="remove_outbound">Remove Selected</button>
            </form>
            <p style="clear: right;"><b><a href="${cfg.basePath}admin/editOutbound">Add an Outbound Mirror</a></b></p>
        </div>
    </body>
</html>
