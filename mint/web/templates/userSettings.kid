<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Edit Account Information: %s'%auth.fullName)}</title>
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
                <div class="right-palette">
                    <img class="left" src="${cfg.staticPath}apps/mint/images/header_user_left.png" alt="" />
                    <img class="right" src="${cfg.staticPath}apps/mint/images/header_user_right.png" alt="" />
                    <div class="rightBoxHeader">
                        <b>Close My Account</b>
                    </div>
                    <div class="rightBoxBody">
                       If you wish to cancel your account, click the &quot;Close My Account&quot; button below.
                       If you cancel your account, you will be removed from any ${projectText().lower()} for which you are
                       a member or owner.
                        <form method="get" action="cancelAccount">
                        <p>    
                            <button class="img" id="userCancel" type="submit"><img src="${cfg.staticPath}/apps/mint/images/cancel_account_button.png" alt="Cancel Account" /></button>
                        </p>
                        </form>
                    </div>
               </div>
            </div>
          <div id="leftcenter">
            <div class="page-title-no-project">
                Edit Account Information
            </div>
            <form method="post" action="editUserSettings">
            <table class="mainformhorizontal">
            <tr>
                <td class="form-label">Username:</td>
                <td class="form-label">${auth.username}</td>
            </tr>
            <tr>
                <td class="form-label">Full Name:</td>
                <td><input type="text" name="fullName" value="${auth.fullName}" /></td>
            </tr>                                                         <tr>
                <td class="form-label">Email Address:</td>
                <td>
                    <input type="text" name="email" value="${auth.email}" />
                    <div class="help">This email address will not be displayed on the ${cfg.companyName} website.</div>
                </td>
            </tr>
            <tr>
                <td class="form-label">Contact Information:</td>
                <td>
                    <textarea rows="4" type="text" name="displayEmail">${auth.displayEmail}</textarea>
                    <div class="help">
                        Contact information provided here will be displayed
                        on your ${cfg.companyName} user information page.
                    </div>
                </td>
            </tr>
            <tr>
                <td class="form-label">Profile Information:</td>
                <td>
                    <textarea rows="8" name="blurb">${auth.blurb}</textarea><br/>
                    <div class="help">
                        Please enter any relevant information about yourself here;
                        a short biography, IRC nicknames, or anything else you would
                        like to share with the ${cfg.productName} community.
                    </div>
                </td>
            </tr>
            </table>
           
            <h2>Change Password</h2>
            <table class="mainformhorizontal">
            <tr>
                <td colspan="2">
                    <div class="help">
                    Please leave these fields blank if you do not want to change your password.</div>
                </td>
            </tr>
            <tr>
                <td class="form-label fields-compact">New Password:</td>
                <td class="fields-compact" style="width:100%"><input class="field-pwd" type="password" name="password1" value="" /></td>
            </tr>
            <tr>
                <td class="form-label fields-compact">Confirm Password:</td>
                <td class="fields-compact" style="width:100%">
                    <input class="field-pwd" type="password" name="password2" value="" />
                    </td>
            </tr>
            </table>
            
            <h2>Package Signing Keys</h2>
            <ul class="pageSectionList">
                <li><a href="http://${SITE}uploadKey">Upload a package signing key</a></li>
            </ul>

        
            <h2>Preferences</h2>
            <table class="mainformhorizontal">
            <tr py:for="key, (dType, default, prompt, errmsg, helpText, password) in sorted(user.getDataTemplate().iteritems())" class="${key in defaultedData and 'attention' or None}">
                <td class="fields-compact" py:if="dType == data.RDT_BOOL" colspan="2"><input type="checkbox" class='check' name="${key}" py:attrs="{'checked' : dataDict.get(key, default) and 'checked' or None}"/> ${prompt}</td>
                <div py:if="dType == data.RDT_INT" py:strip="True">
                <td  class="form-label">
                    ${prompt}</td>
                <td style="width:100%"><input class="field-numeric" type="text" name="$key" value="${dataDict.get(key, default)}"/></td>
                </div>
            </tr>
            </table>
                    <p py:if="(defaultedData or firstTimer) and cfg.tosPostLoginLink">
                       <input type="checkbox" class="check" name="tos" id="tos"/> 
                       <em class="required">I have read and accept the <a href="${cfg.tosPostLoginLink}" title="Terms of Service" target="_blank">Terms of Service</a></em>
                    </p>
                    <button class="img" id="userSubmit" type="submit"><img src="${cfg.staticPath}/apps/mint/images/submit_button.png" alt="Submit" /></button>
        </form>
        </div><br class="clear"/>
        <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
        <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
        <div class="bottom"/>
    </div>
    </body>
</html>
