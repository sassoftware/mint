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
    from mint.web.templatesupport import projectText
?>

    <head>
        <title>${formatTitle('External %ss'%projectText().title())}</title>
    </head>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <div class="page-title-no-project">Externally-Managed ${projectText().title()}s</div>
                <p class="help">Externally-managed ${projectText().lower()}s allow a remote Conary repository to be accessible by
                        this rBuilder. Click on the name of an external ${projectText().lower()} to edit its settings.</p>
                <table class="results">
                    ${columnTitles(regColumns)}
                    ${searchResults(regRows)}
                </table>
    
                <h2>Mirrored ${projectText().title()}s</h2>
                <table class="results">
                    ${columnTitles(mirrorColumns)}
                    ${searchResults(mirrorRows)}
                </table>
                <br />
                <p class="p-button"><a href="addExternal"><b>Add a New External ${projectText().title()}</b></a></p>
                <br />
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
