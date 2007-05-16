<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
<?python
    for var in ['projectId', 'allLabels', 'mirrorSources']:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title>${formatTitle('Add Outbound Mirror')}</title>
    </head>
    <body onload="hideElement('groupTD');">
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/processAddOutbound" method="post">
                <h2>Add Outbound Mirror</h2>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th style="width: 1%;"><em class="required">Project to mirror:</em></th>
                        <td>
                            <select id="projectId" name="projectId" onchange="getGroups(this.value);">
                                <option py:attrs="{'selected': kwargs['projectId'] == project[0] and 'selected' or None}"
                                        py:for="project in projects" value="${project[0]}">${project[2]}</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">Mirror by:</em></th>
                        <td>
                            <input value="label" style="width:auto;" type="radio" name="mirrorBy" checked="true" onclick="hideElement('groupTD'); showElement('submitButton');"/>Label
                            <input id="mirrorByGroup" value="group" style="width:auto;" type="radio" name="mirrorBy" onclick="showElement('groupTD'); getGroups(getElement('projectId').value);"/>Group<br/>
                        </td>
                    </tr>
                    <tr>
                        <th></th>
                        <td>
                        <div id="groupTD">
                        <table>
                        <th>Select group to mirror</th>
                        <td>
                            <select name="groups" id="groups">
                            </select>
                        </td>
                <td>
                <div id="spinner" style="display: none;">
                    <img src="${cfg.staticPath}/apps/mint/images/circle-ball-dark-antialiased.gif"/>
                </div>
                </td>
                        </table>
                        </div>
                        </td>
                    </tr>
                    <tr>
                        <th rowspan="3">Mirroring options:</th>
                        <td>
                            <input py:attrs="{'checked': kwargs['mirrorSources'] and 'checked' or None}"
                                   class="check" type="checkbox" name="mirrorSources" value="1" id="mirrorSources" />
                            <label for="mirrorSources">Include source components when mirroring</label>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input py:attrs="{'checked': kwargs['allLabels'] and 'checked' or None}"
                                   class="check" type="checkbox" name="allLabels" value="1" id="allLabels" />
                            <label for="allLabels">Include all labels when mirroring</label>
                        </td>
                    </tr>
                </table>
                <button class="img" type="submit" id="submitButton">
                    <img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add" />
                </button>
            </form>
        </div>
    </body>
</html>
