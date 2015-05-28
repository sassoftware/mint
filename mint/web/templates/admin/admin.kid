<?xml version='1.0' encoding='UTF-8'?>
<?python
    from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">

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

    <div py:def="adminResourcesMenu" id="admin" class="palette">
        <?python
            lastchunk = req.path[req.path.rfind('/')+1:]
        ?>
        <img class="left" src="${cfg.staticPath}apps/mint/images/header_blue_left.png" alt="" />
        <img class="right" src="${cfg.staticPath}apps/mint/images/header_blue_right.png" alt="" />
        <div class="boxHeader"><span class="bracket">[</span> Administration Menu <span class="bracket">]</span></div>
        <ul class="navigation">
            <li py:attrs="{'class': (lastchunk in ('', 'admin')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/">Administration Home</a></li>
            <li py:attrs="{'class': (lastchunk in ('external', 'addExternal', 'processAddExternal')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/external">Externally-Managed ${projectText().title()}s</a></li>
            <li py:attrs="{'class': (lastchunk in ('updateServices', 'editUpdateService', 'processEditUpdateService')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/updateServices">Configure Update Services</a></li>
            <li py:attrs="{'class': (lastchunk in ('outbound', 'editOutbound', 'processEditOutbound')) and 'selectedItem' or None}"><a href="${cfg.basePath}admin/outbound">Configure Outbound Mirroring</a></li>
        </ul>
    </div>

</html>
