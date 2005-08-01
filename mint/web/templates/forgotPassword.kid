<?xml version='1.0' encoding='UTF-8'?>
<?python
messages = { '':          'If you do not have an account, please <a href="register">register</a>.',
             'confirm':   'Please wait for the confirmation message in your email.',
             'confirmed': 'Your account has been confirmed. Please log in now.',
             'invalid':   'Sorry, the username or password is incorrect.' }
?>

<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head/>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>Please log in to use rpath.com:</h2>
                <p py:if="message" style="font-weight: bold;" py:content="messages[message]"/>
                <form method="post" action="processLogin">
                    <p class="help">
                        If you have forgotten your password, please enter only
                        your username in the field below, and click Forgot Password.
                    </p>
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

                    <p>
                        <button type="submit" name="submit" value="Log In">Log In</button>&#160;
                        <button type="submit" name="submit" value="Forgot Password">Forgot Password</button>
                    </p>
                </form>
            </div>
        </td>
    </body>
</html>
