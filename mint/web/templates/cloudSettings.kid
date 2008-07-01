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
        <title>${formatTitle('Edit Amazon EC2 Settings: %s'%auth.fullName)}</title>
        <?python
            from mint import data
            from mint.web.templatesupport import projectText
        ?>
    </head>
    <body>
        <div id="layout">
            <h2>Edit Amazon EC2 Settings</h2>
            <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form method="post" action="processCloudSettings">

                <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                    <tr py:for="key, (dType, default, prompt, errmsg, helpText, password) in sorted(user.getDataTemplateAWS().iteritems())" class="required">
                        <div py:strip="True" py:if="dType == data.RDT_BOOL">
                            <td colspan="2">
                                <input type="checkbox" class='check' name="${key}" py:attrs="{'checked' : dataDict.get(key, default) and 'checked' or None}"/> 
                                ${prompt}
                                <div py:if="helpText" class="help">
                                    ${helpText}
                                </div>
                            </td>
                        </div>
                        <div py:strip="True" py:if="dType == data.RDT_INT or dType == data.RDT_STRING">
                            <td>${prompt}</td>
                            <td>
                                <input py:if="password" type="password" name="$key" value="${dataDict.get(key, default)}"/>
                                <input py:if="not password" type="text" name="$key" value="${dataDict.get(key, default)}"/>
                                <div py:if="helpText" class="help">
                                    ${helpText}
                                </div>
                            </td>
                        </div>
                    </tr>
                </table>
                <p>
                    <button id="cloudSettingsySubmit" class="img" type="submit">
                        <img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" />
                    </button>
                </p>
            </form>
        </div>
    </body>
</html>
