<?xml version='1.0' encoding='UTF-8'?>
<?python
title = "Login"

messages = { '':          'If you do not have an account, please <a href="register">register</a>.',
             'confirmed': 'Your account has been confirmed. Please log in now.',
             'invalid':   'Sorry, the username or password is incorrect.' }
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header(cfg, title)}
    <body>
        ${header_image(cfg)}
        ${menu([(title, None, True)])}
        
        <div id="content">
        <p>Please log in to use the Specifix custom distribution server:</p>
        <p py:if="message" style="font-weight: bold;" py:content="messages[message]"/>
        <form method="post" action="login2">
            <table>
                <tr>
                    <td><b>Username:</b></td>
                    <td><input type="text" name="username" /></td>
                </tr>
                <tr>
                    <td><b>Password:</b></td>
                    <td><input type="password" name="password" /></td>
                </tr>
            </table>

            <p><input type="submit" value="Log In" /></p>
        </form>
        ${html_footer(cfg)}
        </div>
    </body>
</html>
