<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Create an Account</a>
    </div>

    <head/>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>Create an Account</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="processRegister">

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Username:</em></th>
                            <td>
                                <input type="text" name="username" />
                                 <p class="help">please limit to 16 characters</p>
                            </td>
                        </tr>

                        <tr>
                            <th>Full Name:</th>
                            <td><input type="text" name="fullName" value="${auth.fullName}" /></td>
                        </tr>
                        <tr>
                            <th><em class="required">Email Address:</em></th>
                            <td>
                                <input type="text" name="email" />

                                <p class="help">This email address will not be displayed on the rpath website.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>Contact Information:</th>
                            <td>
                                <textarea rows="3" type="text" name="displayEmail">${auth.displayEmail}</textarea>

                                <p class="help">Contact information provided here will be displayed on your rpath user information page.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>About:</th>
                            <td>
                                <textarea rows="6" name="blurb">${auth.blurb}</textarea><br/>

                                <p class="help">
                                    Please enter any relevant information about yourself here;
                                    a short biography, IRC nicknames, or anything else you would
                                    like to share with the rpath.com community.
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
                    <p>You will receive a confirmation message with a link to activate your account.</p>

                    <p><button type="submit">Register</button></p>
                </form>
            </div>
        </td>
        <td id="right" class="plain">
            <div class="pad">
                <h3>About rpath accounts</h3>
                <p>
                    Using a rpath.com account, you can create your own Linux distribution.
                    Please read the <a href="#">Terms of Service</a> before you register
                    for an account.
                </p>
                <p>
                    Your email address will never be shared or sold. More information
                    can be found in our <a href="#">Privacy Policy</a>.
                </p>
            </div>
        </td>
    </body>
</html>
