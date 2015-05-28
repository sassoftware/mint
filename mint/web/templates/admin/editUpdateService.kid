<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
-->
<?python
    for var in ['updateServiceId', 'hostname', 'mirrorUser', 'mirrorPassword', 'description']:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title py:if="isNew">${formatTitle('Add Update Service')}</title>
        <title py:if="not isNew">${formatTitle('Edit Update Service')}</title>
    </head>
    <body>
    <div class="admin-page">
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="admin-spanright">
            <form action="${cfg.basePath}admin/processEditUpdateService" method="post">
                <div class="page-title-no-project">Add Update Service</div>
                <p>Fill in the form below to set up an rPath Appliance
                   Platform Update Service.</p>
                <p>Note: the target Update Service must be online and
                   network-reachable in order to be added.</p>

                <table class="mainformhorizontal">
                <tr>
                    <td class="form-label"><em class="required">Update Service Hostname:</em></td>
                    <td>
                        <input type="text" name="hostname" maxlength="255" value="${kwargs['hostname']}" />
                        <p class="help">Use the fully-qualified domain name of the target repository or Update Service (example: mirror.rpath.com).</p>
                    </td>
                </tr>
                <tr>
                    <td class="form-label"><em class="optional">Description:</em></td>
                    <td>
                        <textarea name="description" py:content="kwargs['description']"/>
                        <p class="help">A description of this Update Service used for informational purposes only.</p>
                    </td>
                </tr>
                <tr>
                    <td class="form-label"><em class="required">Mirror Username:</em></td>
                    <td><input type="text" name="mirrorUser" style="width: 25%;" value="${kwargs['mirrorUser']}" />
                    </td>
                </tr>
                <tr>
                    <td class="form-label"><em class="required">Mirror Password:</em></td>
                    <td><input autocomplete="off" type="password" name="mirrorPassword" style="width: 25%;" value="${kwargs['mirrorPassword']}" />
                    <p class="help">The above username and password must be a repository user on the target that has 'Mirror' permissions. If the update service is not a mirror you may leave this blank.</p></td>
                </tr>
                </table>
                <br />
                <p>
                    <input id="submitButton" type="submit" name="action" value="Submit" />
                    <input type="submit" name="action" value="Cancel" />
                </p>
                <br />
                <input type="hidden" name="id" value="${id}" />
            </form>
        </div>
        <div class="bottom"/>
    </div>
    </body>
</html>
