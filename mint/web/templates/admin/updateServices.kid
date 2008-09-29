<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Manage Update Services')}</title>
    </head>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <form action="${cfg.basePath}admin/removeUpdateServices" method="post">
                    <div class="page-title-no-project">Manage Update Services</div>
                    <p>Update Services are targets for an Outbound Mirror or
                       publish operation.</p>
    
                    <table py:if="updateServices" class="admin-results">
                    <tr>
                        <th></th>
                        <th>Update Service</th>
                    </tr>
                    <div py:strip="True" py:for="id, hostname, _, _, description in updateServices">
                        <tr class="item-row">
                            <td><input type="checkbox" name="remove" value="${id}" /></td>
                            <td width="100%" style="vertical-align: middle;">
                                <a href="editUpdateService?id=${id}">${hostname}</a>
                                <p py:strip="True" py:if="description" class="help">
                                    ${description}
                                </p></td>
                        </tr>
                    </div>
                    </table>
                    <p>
                    <button py:if="updateServices" type="submit" name="operation" value="remove_updateservice">Remove Selected</button>
                    </p>
                </form>
                <p><a href="${cfg.basePath}admin/editUpdateService">Add an Update Service</a></p>
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
