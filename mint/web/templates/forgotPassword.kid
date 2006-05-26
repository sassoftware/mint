<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Lost Password')}</title>
    </head>
    <body>
        <div id="layout">
            <h2>Lost Password:</h2>
            <form method="post" action="resetPassword">
                <p class="help">
                    If you have forgotten your password, please enter
                    your username in the field below, and click Forgot Password.
                </p>
                <table style="width: 50%; margin-bottom: 1em;">
                    <tr>
                        <td><b>Username:</b></td>
                        <td><input type="text" autocomplete="off" name="username" /></td>
                    </tr>
                </table>
                <p>
                    <button type="submit">Forgot Password</button>
                </p>
            </form>
        </div>
    </body>
</html>
