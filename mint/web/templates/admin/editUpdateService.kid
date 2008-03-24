<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
<?python
    for var in ['updateServiceId', 'hostname', 'adminUser', 'adminPassword', 'description']:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title py:if="isNew">${formatTitle('Add Update Service')}</title>
        <title py:if="not isNew">${formatTitle('Edit Update Service')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/processEditUpdateService" method="post">
                <div py:strip="True" py:if="isNew">
                <h2>Add Update Service</h2>
                <p>Guide text needed for add case.</p>
                </div>

                <div py:strip="True" py:if="not isNew">
                <h2>Edit Update Service</h2>
                <p>Guide text needed for edit case.</p>
                </div>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th><em class="required">Update Service Hostname</em></th>
                        <td>${kwargs['hostname']}</td>
                    </tr>
                    <tr>
                        <th><em class="optional">Description</em></th>
                        <td>
                            <textarea name="description" py:content="kwargs['description']"/>
                            <p class="help">A description of this Update Service used for informational purposes only.</p>
                        </td>
                    </tr>
                    <tr py:if="isNew">
                        <th><em class="required">Update Service Username:</em></th>
                        <td><input type="text" name="adminUser" style="width: 25%;" value="${kwargs['adminUser']}" />
                        </td>
                    </tr>
                    <tr py:if="isNew">
                        <th><em class="required">Update Service Password:</em></th>
                        <td><input autocomplete="off" type="password" name="adminPassword" style="width: 25%;" value="${kwargs['adminPassword']}" />
                        <p class="help">The above username and password must match an administrator's account on the target Update Service.</p></td>
                    </tr>
                </table>
                <p>
                    <input id="submitButton" type="submit" name="action" value="Submit" />
                    <input type="submit" name="action" value="Cancel" />
                </p>
                <input type="hidden" name="id" value="${id}" />
            </form>
        </div>
    </body>
</html>
