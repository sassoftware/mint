<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Edit Amazon Web Services(TM) Settings: %s'%auth.fullName)}</title>
        <?python
            from mint import data
            from mint.web.templatesupport import projectText
        ?>
    </head>
    <body>
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
          <div id="leftcenter">
            <div class="page-title-no-project">
                Amazon Web Services&trade; Settings
            </div>
            
            <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form method="post" action="processCloudSettings">

                <table class="mainformhorizontal">
                <tr py:for="key, (dType, default, prompt, errmsg, helpText, password) in sorted(user.getDataTemplateAWS().iteritems())">
                    <div py:strip="True" py:if="dType == data.RDT_BOOL">
                        <td colspan="2">
                            <input type="checkbox" class='check' name="${key}" py:attrs="{'checked' : dataDict.get(key, default) and 'checked' or None}"/> 
                            <em class="form-label required">${prompt}</em>
                            <div py:if="helpText" class="help">
                                ${helpText}
                            </div>
                        </td>
                    </div>
                    <div py:strip="True" py:if="dType == data.RDT_INT or dType == data.RDT_STRING">
                        <td class="form-label"><em class="required">${prompt}</em></td>
                        <td>
                            <input py:attrs="{'type': (password and 'password' or 'text'), 'name': key, 'value': dataDict.get(key, default)}" name="$key" value="${dataDict.get(key, default)}"/>
                            <div py:if="helpText" class="help">
                                ${helpText}
                            </div>
                        </td>
                    </div>
                </tr>
                </table>
                <p class="p-button">
                    <button id="cloudSettingsySubmit" class="img" type="submit">
                        <img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" />
                    </button>
                </p>
            </form>
        </div><br class="clear"/>
        <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
        <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
        <div class="bottom"/>
    </div>
    </body>
</html>