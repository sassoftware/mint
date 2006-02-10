<?xml version='1.0' encoding='UTF-8'?>
<?python
from conary.lib.cfg import *
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('rBuilder Product Setup')}</title>
    </head>
    <body>
        <div class="layout">
            <h1>rBuilder Product Setup</h1>

            <p class="message" py:if="errors">
                <p py:for="error in errors" py:content="error" />
            </p>

            <form action="processSetup" method="post">
                <div py:for="group, groupItems in configGroups.items()">
                    <h2>${group}</h2>
                    <table class="setup">
                        <tr py:for="i, key in enumerate(groupItems)">
                            <td>
                                ${XML(newCfg._options[key].__doc__ and newCfg._options[key].__doc__ or key)}
                            </td>
                            <td py:if="isinstance(newCfg._options[key].valueType, CfgBool)">
                              <input class="check" type="checkbox" name="${key}" value="${newCfg.__dict__[key]}"/>
                            </td>
                            <td py:if="isinstance(newCfg._options[key].valueType, CfgString)">
                              <input style="width: 100%;" type="text" name="${key}" value="${newCfg.__dict__[key]}"/>
                            </td>
                        </tr>
                    </table>
                </div>
                <h2>Administrator User</h2>
                <table class="setup">
                    <tr>
                        <td>Please enter a username to create the initial administrator account:</td>
                        <td>
                            <input type="text" name="new_username" />
                        </td>
                    </tr>
                    <tr>
                        <td>New Password:</td>
                        <td>
                            <input type="password" name="new_password" />
                        </td>
                    </tr>
                    <tr>
                        <td>New password again:</td>
                        <td>
                            <input type="password" name="new_password2" />
                        </td>
                    </tr>
                    <tr>
                        <td>Administrator's email address:</td>
                        <td>
                            <input type="text" name="new_email" />
                        </td>
                    </tr>
                </table>

            <p><button type="submit">Save Changes</button></p>
          </form>
        </div>
    </body>
</html>
