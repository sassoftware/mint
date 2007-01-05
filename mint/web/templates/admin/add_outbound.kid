<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
<?python
    for var in ['projectId', 'targetUrl', 'mirrorUser',
        'mirrorPass', 'mirrorSources', 'allLabels']:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title>${formatTitle('Add Outbound Mirror')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/processAddOutbound" method="post">
                <h2>Add Outbound Mirror</h2>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th><em class="required">Project to mirror:</em></th>
                        <td>
                            <select name="projectId">
                                <option py:attrs="{'selected': kwargs['projectId'] == project[0] and 'selected' or None}"
                                        py:for="project in projects" value="${project[0]}">${project[2]}</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">URL of target repository:</em></th>
                        <td>
                            <input type="text" autocomplete="off" name="targetUrl" maxlength="255" value="${kwargs['targetUrl']}"/>
                            <p class="help">Use the full URL of the target repository.
                                If the target repository requires the use of SSL, be sure to use https://.
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <th><em class="required">Username:</em></th>
                        <td><input autocomplete="off" type="text" name="mirrorUser" style="width: 25%;" value="${kwargs['mirrorUser']}" /></td>
                    </tr>
                    <tr>
                        <th><em class="required">Password:</em></th>
                        <td><input autocomplete="off" type="password" name="mirrorPass" style="width: 25%;" value="${kwargs['mirrorPass']}" /></td>
                    </tr>
                    <tr>
                        <td colspan="2"><hr /></td>
                    </tr>
                    <tr>
                        <th rowspan="2">Mirroring options:</th>
                        <td>
                            <input py:attrs="{'checked': kwargs['mirrorSources'] and 'checked' or None}"
                                   class="check" type="checkbox" name="mirrorSources" value="1" id="mirrorSources" />
                            <label for="mirrorSources">Mirror source components to target repository.</label>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <input py:attrs="{'checked': kwargs['allLabels'] and 'checked' or None}"
                                   class="check" type="checkbox" name="allLabels" value="1" id="allLabels" />
                            <label for="allLabels">Mirror all labels to the target repository,
                                rather than only the default project label.</label>
                        </td>
                    </tr>
                </table>
                <button class="img" type="submit">
                    <img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add" />
                </button>
            </form>
        </div>
    </body>
</html>
