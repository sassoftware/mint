<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Edit Account Information: %s'%auth.fullName)}</title>
    </head>
    <body>
        <div class="layout">
            <div id="right" class="side">
                ${resourcePane()}
                <div style="width: 180px;">
                    <h3>Close My Account</h3>
                    <p>If you wish to cancel your account, click the &quot;cancel account&quot; button below.
                       If you cancel your account, you will be removed from any project for which you are
                       a member or owner.
                    </p>
                    <p>
                        <form method="get" action="cancelAccount">
                            <button class="warn" type="submit">Cancel my account</button>
                        </form>
                    </p>
                </div>
            </div>

            <div id="spanleft">
                <form method="post" action="editUserSettings">
                    <h2>Edit Account Information</h2>
                    <table class="mainformhorizontal">
                        <tr>
                            <th>Username:</th>
                            <td>${auth.username}</td>
                        </tr>
                        <tr>
                            <th>Full Name:</th>
                            <td><input type="text" name="fullName" value="${auth.fullName}" /></td>
                        </tr>                                                         <tr>
                            <th>Email Address:</th>
                            <td>
                                <input type="text" name="email" value="${auth.email}" />
                                <div class="help">This email address will not be displayed on the ${cfg.companyName} website.</div>
                            </td>
                        </tr>
                        <tr>
                            <th>Contact Information:</th>
                            <td>
                                <textarea rows="4" type="text" name="displayEmail">${auth.displayEmail}</textarea>
                                <div class="help">
                                    Contact information provided here will be displayed
                                    on your ${cfg.companyName} user information page.
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <th>About:</th>
                            <td>
                                <textarea rows="8" name="blurb">${auth.blurb}</textarea><br/>
                                <div class="help">
                                    Please enter any relevant information about yourself here;
                                    a short biography, IRC nicknames, or anything else you would
                                    like to share with the ${cfg.productName} community.
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2">
                                <p><strong>Change Password</strong><br />
                                    Please leave these fields blank if you do not want to change your password:
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th>New Password:</th>
                            <td><input type="password" name="password1" value="" /></td>
                        </tr>
                        <tr>
                            <th>Confirm Password:</th>
                            <td><input type="password" name="password2" value="" /></td>
                        </tr>
                        <tr>
                            <td colspan="2">
                                <p><strong>Package Signing Keys:</strong>
                                <a href="/uploadKey">Upload a package signing key</a></p>
                            </td>
                        </tr>
                    </table>
                    <p><button type="submit">Submit</button></p>
                </form>
            </div>
        </div>
    </body>
</html>
