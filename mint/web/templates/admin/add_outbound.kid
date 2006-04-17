<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Add Outbound Mirror')}</title>
    </head>
    <body>
        <div class="layout">
            <form action="${cfg.basePath}admin/processAddOutbound" method="post">
                <h2>Add Outbound Mirror</h2>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th><em class="required">Project to mirror:</em></th>
                        <td>
                            <select name="projectId">
                                <option py:for="project in projects" value="${project[0]}">${project[3]}</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">URL of target repository:</em></th>
                        <td>
                            <input type="text" name="targetUrl" maxlength="255" value=""/>
                            <p class="help">Use the full URL of the target repository.
                                If the target repository requires the use of SSL, be sure to use https://.
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <th><em class="required">Username:</em></th>
                        <td><input type="text" name="mirrorUser" style="width: 25%;" /></td>
                    </tr>
                    <tr>
                        <th><em class="required">Password:</em></th>
                        <td><input type="password" name="mirrorPass" style="width: 25%;" /></td>
                    </tr>
                </table>
                <button class="img" type="submit">
                    <img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add" />
                </button>
            </form>
        </div>
    </body>
</html>
