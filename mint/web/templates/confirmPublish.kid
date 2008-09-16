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
        <div class="fullpage">
            <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            
            <div class="full-content">
                <div class="page-title-no-project">Confirm:</div>
            
                <p>${message}</p>
                <form method="post" action="${yesArgs['func']}">
                <table class="not-wide">
                <tr py:if="mirroredByRelease">
                    <td>
                    <label>
                        <input id="shouldMirror" name="shouldMirror" class="check" type="checkbox"
                            value="1" py:attrs="{'checked': shouldMirror and 'checked' or None}" />
                        Publish this release to the Update Service
                    </label>
                    </td>
                </tr>
                <tr>
                    <td>
                        <a class="imageButton" href="${noLink}"><img src="${cfg.staticPath}apps/mint/images/no_button.png" alt="No" /></a>
                    </td>
                    <td>
                        <span py:for="k, v in yesArgs.iteritems()">
                          <input type="hidden" name="${k}" value="${v}"/>
                        </span>
                        <button class="img" id="yes" type="submit">
                            <img src="${cfg.staticPath}apps/mint/images/yes_button.png" alt="Yes" /></button>
                    </td>
                </tr>
                </table>
                
                <div py:strip="True" py:if="previewData">
                    <div>
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
                        </table>
                        </div>
                    </div>
                </div>
            </form>
            </div>
            <br class="clear"/>
            <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
            <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
            <div class="bottom"/>
        </div>
    </body>
</html>
