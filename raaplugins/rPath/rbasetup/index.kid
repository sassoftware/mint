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
Copyright (c) 2008-2009 rPath, Inc.
    All Rights Reserved
-->

<?python
    if not configured:
        pageTitle = "Initial rBuilder Setup"
        instructions = "Finish configuring your rBuilder Appliance by providing the following information. Some fields have been populated with default values; these can be changed if necessary."
        advancedOptionsUrl = makeUrl('/static/images/icon_expand.gif')
        advancedOptionsStyle = 'display: none;'
    else:
        pageTitle = "rBuilder Setup"
        instructions = "Change the following fields to modify your rBuilder Appliance's configuration."
        advancedOptionsUrl = makeUrl('/static/images/icon_collapse.gif')
        advancedOptionsStyle = ''
?>
<head>
    <title>${getConfigValue('product.productName')}: ${pageTitle}</title>
    <style type="text/css">
        <![CDATA[
            .rbasetup-label {
                float: left;
                width: 220px;
                white-space: nowrap;
                padding-top: 3px;
            }
        ]]>
    </style>
    <script type="text/javascript">
        <![CDATA[
            function postFormRedirectFirstTimeSetupOnSuccess(form, url) {
                var d = postFormData(form, url);
                d = d.addCallback(callbackCheckError);
                if(${not configured and "true" or "false"}) {
                    d = d.addCallback(createCallbackRedirect("${makeUrl('firstTimeSetup')}"));
                } else {
                    d = d.addCallback(callbackMessage);
                }
                d = d.addErrback(callbackErrorGeneric);
            }

            expand_h = "${makeUrl('/static/images/icon_expand_h.gif')}";
            expand = "${makeUrl('/static/images/icon_expand.gif')}";
            collapse_h = "${makeUrl('/static/images/icon_collapse_h.gif')}";
            collapse = "${makeUrl('/static/images/icon_collapse.gif')}";
            function toggleAdvanced(link, expand, collapse, element) {
                var el = $(element);
                if(link.src.match("expand")) {
                    link.src = collapse;
                    el.style.display = '';
                    normal = collapse;
                    hover = collapse_h;
                } else {
                    link.src = expand;
                    el.style.display = 'none';
                    normal = expand;
                    hover = expand_h;
                }
            }
        ]]>
    </script>
</head>

<body>
    <div class="plugin-page" id="plugin-page">
        <div class="page-content">
            <div py:replace="display_instructions(instructions, raaInWizard)" />
                <form id="page_form" name="page_form" action="javascript:void(0);" method="post" onsubmit="javascript:postFormRedirectFirstTimeSetupOnSuccess(this,'saveConfig');">
                <div py:if="not configured" class="page-section">Initial Administrator Account</div>
                <div py:if="not configured" class="page-section-content">
                    <p>
                        Provide details for your rBuilder administrator
                        account. This account is used to access rBuilder's web
                        interface, and is separate from the account used to
                        access the rPath Platform Agent for maintenance of your
                        rBuilder Appliance. The Agent password will initially
                        also be set to the password you provide here; if you
                        wish to make the Agent password different from the
                        rBuilder administrator password, you must change the
                        Agent password later.
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
                        displayed below are based on the URL you used to
                        access your rBuilder Appliance.  You can change
                        these values, but be aware that the resulting
                        fully-qualified domain name (FQDN) constructed from
                        the values you've entered must match the URL your
                        users will use to access rBuilder.
                    </p>
                    <div class="form-line-top">
                        <div class="rbasetup-label">rBuilder Appliance's FQDN:</div>
                        <input type="text" name="hostName" value="${hostName}" />
                    </div>
                        <p>
                            Choose a default domain name for project
                            repositories. This will be visible in package
                            version information, and should usually be your
                            organization's external domain.
                        </p>
                    <div class="form-line">
                        <div class="rbasetup-label">Default project domain name:</div>
                        <input type="text" name="projectDomainName" value="${projectDomainName}" />
                    </div>
                        <p>
                            Choose a default namespace related to your
                            organization's name. This will be visible in
                            package version information, and should usually
                            be related to your organization's name. For
                            example, if your organization's name is "XYZ
                            Incorporated", a namespace of "xyz" would be
                            appropriate.
                        </p>
                    <div class="form-line">
                        <div class="rbasetup-label">Default namespace:</div>
                        <input type="text" name="namespace" value="${namespace}" py:attrs="{'disabled': not allowNamespaceChange and 'disabled' or None}" />
                    </div>
                </div>

               <div class="page-section">Advanced Options
		  <img src="${advancedOptionsUrl}" onclick="javascript:toggleAdvanced(this, expand, collapse, 'advanced_options')" style="cursor: pointer; vertical-align: text-top; padding-right: 4px;" onMouseOver="this.src = this.src.match('expand') ? expand_h : collapse_h" onMouseOut="this.src = this.src.match('expand') ? expand : collapse"/>
                </div>
                <div class="page-section-content">
                    <div id="advanced_options" style="${advancedOptionsStyle}">
	                
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
                        <div class="rbasetup-label">Authentication Cache TTL (sec):</div>
                        <input type="text" name="authCacheTimeout" value="${authCacheTimeout}" />
                    </div>
                    <h3>Repository Options</h3>
                    <div class="form-line">
                        <div class="rbasetup-label">Require OpenPGP-signed commits:</div>
                        <input type="checkbox" name="requireSigs" value="1"
                            py:attrs="{'checked': requireSigs and 'checked' or None}" />
                    </div>
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
