<?xml version='1.0' encoding='UTF-8'?>
<?python
title = "Register"
email = None
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header(cfg, title)}
    <body>
        ${header_image(cfg)}
        ${menu([("Register", None, True)])}
        
        <div id="content">
            <h2>Register</h2>
            <p>Using an rMill account, you can create your own Linux distribution.</p> 

            <form method="post" action="register2">
                <table>
                    <tr><td><b>Username:</b></td><td><input type="text" size="32" name="username" /></td></tr>
                    <tr><td><b>Email address:</b></td><td><input size="32" type="text" name="email" /></td></tr>
                    <tr><td><b>Password:</b></td><td><input type="password" name="password" /></td></tr>
                    <tr><td><b>Confirm Password:</b></td><td><input type="password" name="password2" /></td></tr>
                </table>
                <p>
                    You will receive a confirmation message with a link to activate your account, as
                    well as a temporary password. Your email address will never be shared or sold.
                </p>
                <p><input type="submit" value="Register" /></p>
            </form>

            ${html_footer(cfg)}
        </div>
    </body>
</html>
