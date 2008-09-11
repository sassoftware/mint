<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.helperfuncs import formatProductVersion
?>
    <head>
        <title>${formatTitle('Update Appliance Platform for %s Version %s'% (productName, versionName))}</title>
    </head>

    <body>
        <div id="layout">
            <h2>Update Appliance Platform for ${productName} Version ${versionName}</h2>

            <form id="processRebaseProductVersion" method="post" action="processRebaseProductVersion">
                <table border="0" cellspacing="0" cellpadding="0"
                    class="mainformhorizontal">
                    <tr>
                        <th>Appliance Platform:</th>
                        <td>
                            <select name="platformLabel">
                                <option py:for="platformLabel, platformDesc in availablePlatforms" py:attrs="{'selected': (currentPlatformLabel == platformLabel) and 'selected' or None}" value="${platformLabel}" py:content="platformDesc" />
                                <option py:if="customPlatform" py:attrs="{'selected': (currentPlatformLabel == customPlatform[0]) and 'selected' or None}" value="${customPlatform[0]}" py:content="customPlatform[1]" />
                            </select>
                            <p class="help">
                                The appliance platform is locked to a specific version
                                and will not change unless you update it. By clicking
                                <u>Update Appliance Platform</u> the latest version of
                                the appliance platform currently available will be
                                used in all subsequent builds of the
                                ${productName} version
                                ${formatProductVersion(versions, currentVersion)}
                                appliance. Additionally, you may change
                                the appliance platform on which this version is based.
                            </p>
                        </td>
                    </tr>
                </table>
                <p>
                    <input type="submit" id="submitButton" name="action" value="Update Appliance Platform" />
                    <input type="submit" id="submitButton" name="action" value="Cancel" />
                    <input type="hidden" name="id" value="${id}" />
                </p>
            </form>
        </div>
    </body>
</html>
