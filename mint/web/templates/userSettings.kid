<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("User Settings")}
    <body>
        ${header_image()}
        ${menu([('User Settings', None, True)])}
        <div id="content">
            <h2>User Settings:</h2>

            <form method="post" action="editUserSettings">
                <table style="width: 100%;">
                    <tr>
                        <td>Username:</td>
                        <td>${auth.username}</td>
                    </tr>
                    <tr>
                        <td style="width: 20%;">Full Name:</td>
                        <td><input type="text" name="fullName" value="${auth.fullName}" /></td>
                    </tr>
                    <tr>
                        <td>Email (hidden):<p class="help">This email address is private and will never be displayed.</p></td>
                        <td><input type="text" name="email" value="${auth.email}" /></td>
                    </tr>
                    <tr>
                        <td>Email (displayed):<p class="help">You can specify a spam-masked and/or an alternate email address for public
                                                              view here.</p></td>
                        <td><input type="text" name="displayEmail" value="${auth.displayEmail}" /></td>
                    </tr>

                    <tr>
                        <td>
                            About:
                            <p class="help">Please enter any relevant information about yourself here; a short biography, IRC nicknames,
                                or anything else you would like to share with the rpath.com community.
                            </p>
                        </td>
                        <td>
                            <textarea style="width: 50%;" rows="12" name="blurb" py:content="auth.blurb" />
                        </td>
                    </tr>

                    <tr><td colspan="2"><p class="help">Please leave these fields blank if you do not want to change your password:</p></td></tr>
                    <tr>
                        <td style="padding-top: 25px;">
                            Password:
                        </td>
                        <td style="vertical-align: bottom;"><input type="password" name="password1" value="" /></td>
                    </tr>
                    <tr>
                        <td>Password (again):</td>
                        <td><input type="password" name="password2" value="" /></td>
                    </tr>
                </table>

                <p><input type="submit" value="Submit" /></p>
            </form>
            ${html_footer()}
        </div>
    </body>
</html>
