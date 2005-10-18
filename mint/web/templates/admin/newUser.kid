<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="administer?operation=user">User Administration</a>
        <a href="#">Create an Account</a>
    </div>
    <?python
        for var in ['username', 'email', 'fullName', 'displayEmail', 'blurb', 'tos', 'privacy']:
            kwargs[var] = kwargs.get(var, '')
    ?>
    <head>
        <title>${formatTitle('Create an Account')}</title>
    </head>
    <body>
        <td id="left" class="plain">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
            </div>
        </td>

       <td id="main" class="spanright">
            <div class="pad">
                <p py:if="errors" class="error">Account Creation Error${len(errors) > 1 and 's' or ''}</p>
                <p py:for="error in errors" class="errormessage" py:content="error"/>
                <h2>Create an Account</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="administer?operation=user_register">

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Username:</em></th>
                            <td>
                                <input type="text" name="username" maxlength="16" value="${kwargs['username']}"/>
                                 <p class="help">please limit to 16 characters</p>
                            </td>
                        </tr>

                        <tr>
                            <th>Full Name:</th>
                            <td><input type="text" name="fullName" value="${kwargs['fullName']}" /></td>
                        </tr>
                        <tr>
                            <th><em class="required">Email Address:</em></th>
                            <td>
                                <input type="text" name="email" value="${kwargs['email']}"/>

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
                                <input type="password" name="password" value="" />
                                <p class="help">must be at least 6 characters</p>

                            </td>
                        </tr>
                        <tr>
                            <th><em class="required">Confirm Password:</em></th>
                            <td><input type="password" name="password2" value="" /></td>
                        </tr>
                    </table>
                    <p><button type="submit">Register</button></p>
                </form>
            </div>
        </td>
    </body>
</html>
