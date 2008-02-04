<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
from mint.web.templatesupport import projectText
?>

    <head>
        <title>${formatTitle('Please Confirm')}</title>
        <script type="text/javascript">
            function toggleInfo() {
                if (getElement('vmtn').checked) {
                    showElement('previewInfo');
                }
                else {
                    hideElement('previewInfo');
                }
            }
        </script>

    </head>
    <body>
        <div id="layout">
            <h2>Confirm:</h2>

            <p>${message}</p>
                    <form method="post" action="${yesArgs['func']}">
            <table>
                <tr><td>
                    <p style="width: 50%;">
                        <a class="imageButton" href="${noLink}"><img src="${cfg.staticPath}apps/mint/images/no_button.png" alt="No" /></a>
                    </p>
                </td>
                <td>
                        
                        <span py:for="k, v in yesArgs.iteritems()">
                          <input type="hidden" name="${k}" value="${v}"/>
                        </span>
                        <p style="width: 50%;">
                        <button class="img" id="yes" type="submit"><img src="${cfg.staticPath}apps/mint/images/yes_button.png" alt="Yes" /></button>
                    </p>
                </td><td width="50%"/></tr>
            </table>
                        <div py:strip="True" py:if="previewData">
                            <div style="padding-left: 10px;">
                           <input id="vmtn" type="checkbox" checked="true" name="vmtn" onclick="toggleInfo();"/><label for="vmtn">Submit this release as a community appliance to the <a href="https://www.vmware.com/vmtn/appliances/directory">VMware(R) Virtual
Appliance Marketplace</a></label>                            
                            <div id="previewInfo">
                            <table style="border: 1px solid grey; width: 90%; margin-top: 20px;">
                                <tr>
                                    <td colspan="2">
                                        <p class="help" style="text-align: center;">The following information about your appliance will be posted to the VMware(R) Virtual Appliance Marketplace:</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="text-align: right; padding-right: 30px;">Title:</td>
                                    <td>${previewData['title']}</td>
                                </tr>
                                <tr>
                                    <td  style="text-align: right; padding-right: 30px;">Release Description:</td>
                                    <td>${previewData['oneLiner']}</td>
                                </tr>
                                <tr>
                                    <td style="text-align: right; padding-right: 30px;">${projectText().title()} Description:</td>
                                    <td>${previewData['longDesc']}</td>
                                </tr>
                                <tr><td/></tr>
                            </table>
                            <br/>
                            </div>
                           </div>
                        </div>
                    </form>
        </div>
    </body>
</html>
