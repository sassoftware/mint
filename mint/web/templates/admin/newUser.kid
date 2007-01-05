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
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <h2>Create an Account</h2>
            <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form method="post" action="${cfg.basePath}admin/processNewUser">

                <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                    <tr>
                        <th><em class="required">Username:</em></th>
                        <td>
                            <input type="text" autocomplete="off" name="newUsername" maxlength="16" value="${kwargs['username']}"/>
                             <p class="help">please limit to 16 characters</p>
                        </td>
                    </tr>

                    <tr>
                        <th>Full Name:</th>
                        <td><input type="text" autocomplete="off" name="fullName" value="${kwargs['fullName']}" /></td>
                    </tr>
                    <tr>
                        <th><em class="required">Email Address:</em></th>
                        <td>
                            <input type="text" autocomplete="off" name="email" value="${kwargs['email']}"/>

                            <p class="help">This email address will not be displayed on the ${cfg.companyName} website.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>Contact Information:</th>
                        <td>
                            <textarea rows="3" type="text" name="displayEmail">${kwargs['displayEmail']}</textarea>

                            <p class="help">Contact information provided here will be displayed on your ${cfg.companyName} user information page.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>About:</th>
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
                        <th><em class="required">New Password:</em></th>
                        <td>
                            <input type="password" autocomplete="off" name="password" value="" />
                            <p class="help">must be at least 6 characters</p>

                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">Confirm Password:</em></th>
                        <td><input type="password" autocomplete="off" name="password2" value="" /></td>
                    </tr>
                </table>
                <p><button type="submit">Create New User</button></p>
            </form>
        </div>
    </body>
</html>
