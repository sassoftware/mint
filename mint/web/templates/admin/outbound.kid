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
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <form action="${cfg.basePath}admin/removeOutbound" method="post">
                    <div class="page-title-no-project">Outbound Mirrored ${projectText().title()}s</div>
                    <p class="help">
                        You can select ${projectText().lower()}s in ${cfg.productName} to be mirrored out to
                        an external Conary repository or Update Service.
                    </p>
    
                    <table py:if="rows" class="admin-results">
                    <tr>
                        <th></th>
                        <th>${projectText().title()}</th>
                        <th>Targets</th>
                        <th>Include Sources</th>
                        <th>Order</th>
                    </tr>
                    <div py:strip="True" py:for="data in rows">
                        <tr class="item-row">
                            <td><input type="checkbox" name="remove" value="${data.get('id')}" /></td>
                            <td style="padding-top: 4px;padding-bottom: 4px;">
                                <a href="editOutbound?id=${data.get('id')}">${data.get('projectName')}</a>
                                <br />
                                <div>
                                  <span py:if="not data['groups']" py:strip="True">&nbsp;&nbsp;&nbsp;&nbsp;All packages<br /></span>
                                  <div py:for="g in data.get('groups',[])" py:strip="True">${g}<br /></div>

                                  <span py:if="data['allLabels']" py:strip="True">&nbsp;&nbsp;&nbsp;&nbsp;All labels</span>
                                  <div py:for="l in data.get('labels', [])" py:strip="True">&nbsp;&nbsp;&nbsp;&nbsp;${l}<br /></div>
                                </div>
                            </td>
                            <td style="padding-top: 4px;"><div py:if="not data.get('targets', [])" style="color: red;">No targets defined</div><div py:for="tId, tUrl in data.get('targets', [])">${tUrl}<br /></div></td>
                            <td style="padding-top: 4px;" py:content="data.get('mirrorSources') and 'Yes' or 'No'" />
                            <td style="padding-top: 4px;" py:content="data.get('orderHTML')" />
                            
                        </tr>
                    </div>
                    </table>
                    <p>
                    <button py:if="rows" type="submit" name="operation" value="remove_outbound">Remove Selected</button>
                    </p>
                </form>
                <p style="clear: right;"><a href="${cfg.basePath}admin/editOutbound">Add an Outbound Mirror</a></p>
                <br />
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
