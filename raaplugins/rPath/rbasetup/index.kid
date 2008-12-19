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

<?python
    if not configured:
        pageTitle = "Initial rBuilder Setup"
        instructions = "Now it's time to configure your rBuilder Appliance.  Some of the following fields have been populated with default values, which you may change if necessary."
    else:
        pageTitle = "rBuilder Setup"
        instructions = "Your rBuilder Applinace is already configured. You may make a limited number of changes to the setup via the form below."
?>
<head>
    <title>${getConfigValue('product.productName')}: ${pageTitle}</title>
    <style type="text/css">
        .rbasetup-label {
            float: left;
            width: 220px;
            white-space: nowrap;
            padding-top: 3px;
        }
    </style>
</head>

<body>
    <div class="plugin-page" id="plugin-page">
        <div class="page-content">
            <div py:replace="display_instructions(instructions, raaInWizard)" />
            <form id="page_form" name="page_form" action="javascript:void(0);" method="post"
                onsubmit="javascript:postFormWizardRedirectOnSuccess(this,'doSetup');">
                <div py:if="not configured" class="page-section">Initial Administrator Account</div>
                <div py:if="not configured" class="page-section-content">
                    <p>
                        In order to access the web interface for rBuilder, you will
                        need to create an administrator account. This account is
                        separate from the account you use to access the rPath
                        Platform Agent.
                    </p>
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
                <div class="page-section" py:if="not configured">Server Setup</div>
                <div class="page-section-content" py:if="not configured">
                    <p>
                        <strong>Note:</strong> The hostname and domain name
                        displayed below are based on the URL you used to access your
                        rBuilder server.  You may change these values, but be aware
                        that the resulting fully-qualified domain name constructed from
                        the values you've entered must match the URL your users will
                        use to access rBuilder.
                    </p>
                    <div class="form-line-top">
                        <div class="rbasetup-label">rBuilder Appliance's FQDN:</div>
                        <input type="text" name="hostName" value="${hostName}" />&nbsp;.&nbsp;<input type="text" name="siteDomainName" value="${siteDomainName}" />
                    </div>
                    <div class="form-line">
                        <div class="rbasetup-label">Default repository namespace:</div>
                        <input type="text" name="namespace" value="${namespace}" py:attrs="{'disabled': not allowNamespaceChange and 'disabled' or None}" />
                    </div>
                </div>

                <div class="page-section">Advanced Options</div>
                <div class="page-section-content">
                    <h3>External Authentication</h3>
                    <p>
                        The following options are only required for situations
                        where you wish to use an external URL to handle authentication
                        of rBuilder accounts.
                    </p>
                    <div class="form-line-top">
                        <div class="rbasetup-label">External Authentication URL:</div>
                        <input type="text" name="externalPasswordURL" value="${externalPasswordURL}" />
                    </div>
                    <div class="form-line">
                        <div class="rbasetup-label">Authentication cache TTL (seconds):</div>
                        <input type="text" name="authCacheTimeout" value="${authCacheTimeout}" />
                    </div>
                    <h3>Repository Options</h3>
                    <div class="form-line">
                        <div class="rbasetup-label">Require OpenPGP-signed commits:</div>
                        <input type="checkbox" name="requireSigs" value="1"
                            py:attrs="{'checked': requireSigs and 'checked' or None}" />
                    </div>
                </div>
                <input type="hidden" name="configured" value="${int(configured)}" />
                <input type="hidden" name="allowNamespaceChange" value="${int(allowNamespaceChange)}" />
            </form>

            <div class="page-section-content-bottom">
                <a class="rnd_button float-right" id="OK" href="javascript:button_submit(document.page_form)">${raaInWizard and "Continue" or "Save"}</a>
            </div>
        </div>
    </div>
</body>
</html>
