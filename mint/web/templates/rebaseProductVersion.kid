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

            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>
                <div id="middle">

                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <h2>Update Appliance Platform for ${productName} Version ${versionName}</h2>

                    <form id="processRebaseProductVersion" method="post" action="processRebaseProductVersion">
                        <table class="mainformhorizontal">
                            <tr>
                                <td class="form-label">
                                    Appliance Platform:
                                </td>
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
                            <input type="hidden" name="return_to" value="${return_to}" />
                        </p>
                    </form>
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
