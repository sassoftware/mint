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
        <title>${formatTitle('rBuilder Configuration')}</title>
    </head>
    <body>
        <div class="layout">
            <h1>rBuilder Configuration</h1>

            <p>Now it's time to configure your rBuilder server.  Some of
            the following fields have been pre-populated with default
            values; you may change them if necessary.</p>

            <p><strong>Note:</strong> The hostname and domain name
            displayed below are based on the URL you used to access your
            rBuilder server.  You may change these values, but be aware
            that the resulting fully-qualified domain name constructed from
            the values you've entered must match the URL your users will
            use to access rBuilder.</p>

            <p>When you've filled in the necessary information, click on
            the "Save Changes" button to save your rBuilder server's
            configuration.</p>

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
                <h2>Initial Administrator Account</h2>
                <table class="setup">
                    <tr>
                        <td>Enter a username for the initial administrator account:</td>
                        <td>
                            <input type="text" name="new_username" />
                        </td>
                    </tr>
                    <tr>
                        <td>Password:</td>
                        <td>
                            <input type="password" name="new_password" />
                        </td>
                    </tr>
                    <tr>
                        <td>Re-enter password:</td>
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
                <h2>Entitlements</h2>
                <table class="setup">
                    <tr>
                        <td>
                            If you received an entitlement string from rPath, please paste it here:
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <textarea name="entitlement" rows="10" cols="72"></textarea>
                        </td>
                    </tr>
                </table>
            <p><button type="submit" class="img"><img src="${cfg.staticPath}apps/mint/images/save_changes_button.png" alt="Save Changes" /></button></p>
          </form>
        </div>
    </body>
</html>
