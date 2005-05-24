<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header(cfg, "User Settings")}
    <body>
        ${header_image(cfg)}
        ${menu([('User Settings', None, True)])}
        <div id="content">
            <h2>Change Password or Email:</h2>

            <form method="post" action="editUserSettings">
                <table>
                    <tr>
                        <td>Name:</td>
                        <td>${auth.fullName}</td>
                    </tr>
                    <tr>
                        <td>Email:</td>
                        <td><input type="text" name="email" value="${auth.email}" /></td>
                    </tr>

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
                    <tr>
                        <td colspan="2">
                            <p class="help">Leave the email field blank to change just the password, and vice-versa.</p>
                        </td>
                    </tr>
                </table>

                <p><input type="submit" value="Submit" /></p>
            </form>
            ${html_footer()}
        </div>
    </body>
</html>
