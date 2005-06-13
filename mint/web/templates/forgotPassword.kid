<?xml version='1.0' encoding='UTF-8'?>
<?python
messages = { '':          'If you do not have an account, please <a href="register">register</a>.',
             'confirm':   'Please wait for the confirmation message in your email.',
             'confirmed': 'Your account has been confirmed. Please log in now.',
             'invalid':   'Sorry, the username or password is incorrect.' }
?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
    ${html_header("Login")}
    <body>
        ${header_image()}
        ${menu([("Login", None, True)])}
        
        <div id="content">
        <p>Please log in to use the the rpath Linux Mint custom distribution server:</p>
        <p>If you do not have an account, please <a href="register">register</a>.</p>
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

            <p><input type="submit" name="submit" value="Log In" /> <input type="submit" name="submit" value="Forgot Password" /></p>
            <p class="help">If you have forgotten your password, please enter only your username above, and click Forgot Password.</p>
        </form>
        ${html_footer()}
        </div>
    </body>
</html>
