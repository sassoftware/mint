<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <?python
        for var in ['username', 'email', 'fullName', 'displayEmail', 'blurb', 'tos', 'privacy']:
            kwargs[var] = kwargs.get(var, '')
    ?>
    <head>
        <title>${formatTitle('Create an Account')}</title>
    </head>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <div class="page-title-no-project">Create an Account</div>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="${cfg.basePath}admin/processNewUser">
    
                    <table class="mainformhorizontal">
                    <tr>
                        <td class="form-label"><em class="required">Username:</em></td>
                        <td>
                            <input type="text" autocomplete="off" name="newUsername" maxlength="16" value="${kwargs['username']}"/>
                             <p class="help">please limit to 16 characters</p>
                        </td>
                    </tr>

                    <tr>
                        <td class="form-label">Full Name:</td>
                        <td><input type="text" autocomplete="off" name="fullName" value="${kwargs['fullName']}" /></td>
                    </tr>
                    <tr>
                        <td class="form-label"><em class="required">Email Address:</em></td>
                        <td>
                            <input type="text" autocomplete="off" name="email" value="${kwargs['email']}"/>

                            <p class="help" py:if="cfg.rBuilderOnline">This email address will not be displayed on the ${cfg.companyName} website.</p>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label">Contact Information:</td>
                        <td>
                            <textarea rows="3" type="text" name="displayEmail">${kwargs['displayEmail']}</textarea>

                            <p class="help">Contact information provided here will be displayed on your ${cfg.companyName} user information page.</p>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label">About:</td>
                        <td>
                            <textarea rows="6" name="blurb">${kwargs['blurb']}</textarea><br/>

                            <p class="help">
                                Please enter any relevant information about yourself here;
                                a short biography, IRC nicknames, or anything else you would
                                like to share with the ${cfg.productName} community.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label"><em class="required">New Password:</em></td>
                        <td>
                            <input type="password" autocomplete="off" name="password" value="" />
                            <p class="help">must be at least 6 characters</p>

                        </td>
                    </tr>
                    <tr>
                        <td class="form-label"><em class="required">Confirm Password:</em></td>
                        <td><input type="password" autocomplete="off" name="password2" value="" /></td>
                    </tr>
                    </table>
                    <br />
                    <p class="p-button"><button class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create New User" /></button></p>
                    <br />
                </form>
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
