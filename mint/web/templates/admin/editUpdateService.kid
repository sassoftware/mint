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
                <p>Fill in the form below to set up an rPath Appliance
                   Platform Update Service.</p>
                <p>Note: the target Update Service must be online and
                   network-reachable in order to be added.</p>
                </div>

                <div py:strip="True" py:if="not isNew">
                <h2>Edit Update Service</h2>
                <p>Update the configured Update Service's properties.
                   Currently you may only update the Update Service's
                   description here.</p>
               <p>In the event that this Update Service's hostname has
                  changed, or if the Update Service itself was reinstalled
                  with no content, you will need to delete this record
                  of the Update Service and recreate it. This will
                  reconfigure the Update Service for proper operation.
                  Additionally, you will need to reassign the existing
                  Outbound Mirror targets as appropriate.</p>
                </div>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th><em py:attrs="{'class': isNew and 'required' or 'optional'}">Update Service Hostname</em></th>
                        <td py:if="isNew">
                            <input type="text" name="hostname" maxlength="255" value="${kwargs['hostname']}" />
                            <p class="help">Use the fully-qualified domain name of the target repository or Update Service (example: mirror.rpath.com).</p>
                        </td>
                        <td py:if="not isNew" py:content="kwargs['hostname']" />

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
