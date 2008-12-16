<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
import raa 
import raa.templates.master 
from raa.web import makeUrl, getConfigValue, inWizardMode
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">

<!--
Copyright (c) 2006-2008 rPath, Inc.
    All Rights Reserved
-->

<head>
    <title>${getConfigValue('product.productName')}: Initial Setup</title>
    <style type="text/css">
        .rbasetup-label {
            float: left;
            width: 120px;
            white-space: nowrap;
            padding-top: 3px;
        }
    </style>
</head>

<body>
    <?python instructions = "Now it's time to configure your rBuilder server.  Some of the following fields have been populated with default values, which you may change if necessary."?>
    <div class="plugin-page" id="plugin-page">
        <div class="page-content">
            <div py:replace="display_instructions(instructions, raaInWizard)" />
            <form id="page_form" name="page_form" action="javascript:void(0);" method="post"
                onsubmit="javascript:postFormWizardRedirectOnSuccess(this,'doSetup');">
                <div class="page-section">Initial Administrator Account</div>
                <div class="page-section-content">
                    <div class="form-line-top">
                        <div class="rbasetup-label">Username:</div>
                        <input type="text" name="new_username" autocomplete="off" />
                    </div>
                    <div class="form-line">
                        <div class="rbasetup-label">Password:</div>
                        <input type="password" name="new_password" autocomplete="off" />
                    </div>
                    <div class="form-line">
                        <div class="rbasetup-label">Re-enter password:</div>
                        <input type="password" name="new_password2" autocomplete="off" />
                    </div>
                    <div class="form-line">
                        <div class="rbasetup-label">Email address:</div>
                        <input type="text" name="new_email" autocomplete="off" />
                    </div>
                </div>
                <div py:strip="True" py:for="group, groupItems in configGroups.items()">
                <div class="page-section" py:content="group" />
                <div class="page-section-content">
                    <div py:if="group == 'Server Setup'" py:strip="True">
                        <p><strong>Note:</strong> The hostname and domain name
                        displayed below are based on the URL you used to access your
                        rBuilder server.  You may change these values, but be aware
                        that the resulting fully-qualified domain name constructed from
                        the values you've entered must match the URL your users will
                        use to access rBuilder.</p>

                        <p py:if="'Server Setup' in configGroups">
                        Once you have created a ${projectText().lower()} on your 
                        rBuilder server, you will no longer be able to change the 
                        hostName or siteDomainName fields.</p>
                    </div>
                    <table>
                        <tr py:for="i, key in enumerate(groupItems)">
                            <?python
                                val, docstring, isBoolean = configurableOptions[key]
                            ?>
                            <td>${XML(docstring)}</td>
                            <td>
                                <input py:if="isBoolean" class="check" type="checkbox" name="${key}" value="${val}"
                                    py:attrs="{'checked': val and 'checked' or None}" />
                                <div py:strip="True" py:if="not isBoolean">
                                <div py:if="key == 'namespace'" py:strip="True">
                                <input py:if="allowNamespaceChange" type="text" name="${item}" value="${val}"/>
                                <span py:if="not allowNamespaceChange" py:strip="True">
                                ${val}
                                <input type="hidden" name="${key}" value="${val}" />
                                </span>
                                </div>
                                <input py:if="key != 'namespace'" type="text" name="${key}" value="${val}" />
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
                </div>
            </form>

            <div class="page-section-content-bottom">
                <a class="rnd_button float-right" id="OK" href="javascript:button_submit(document.page_form)">Continue</a>
            </div>
        </div>
    </div>
</body>
</html>
