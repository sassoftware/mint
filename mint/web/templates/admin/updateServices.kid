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
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/removeUpdateServices" method="post">
                <h2>Manage Update Services</h2>
                <p>
                    Need some guide text here: what is an update service,
                    and what it is used for.
                </p>

                <table py:if="updateServices" cellspacing="0" cellpadding="0" class="results">
                    <tr>
                        <th>Update Service</th>
                        <th>Remove</th>
                    </tr>
                    <div py:strip="True" py:for="id, hostname, _, _, description in updateServices">
                        <tr>
                            <td><a href="editUpdateService?id=${id}">${hostname}</a><div py:strip="True" py:if="description"><br /><div style="font-size: smaller;">${description}</div></div></td>
                            <td><input type="checkbox" name="remove" value="${id}" /></td>
                        </tr>
                    </div>
                </table>
                <button py:if="updateServices" style="float: right;" type="submit" name="operation" value="remove_updateservice">Remove Selected</button>
            </form>
            <p style="clear: right;"><b><a href="${cfg.basePath}admin/editUpdateService">Add an Update Service</a></b></p>
        </div>
    </body>
</html>
