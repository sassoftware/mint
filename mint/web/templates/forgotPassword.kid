<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Login')}</title>
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>Lost Password:</h2>
                <form method="post" action="processLogin">
                    <p class="help">
                        If you have forgotten your password, please enter
                        your username in the field below, and click Forgot Password.
                    </p>
                    <table style="width: 50%; margin-bottom: 1em;">
                        <tr>
                            <td><b>Username:</b></td>
                            <td><input type="text" name="username" /></td>
                        </tr>
                    </table>
                    <p>
                        <button type="submit" name="submit" value="Forgot Password">Forgot Password</button>
                    </p>
                </form>
            </div>
        </td>
    </body>
</html>
