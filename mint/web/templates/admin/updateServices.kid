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
