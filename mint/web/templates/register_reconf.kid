<?xml version='1.0' encoding='UTF-8'?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Confirmation Required')}</title>
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>Thank you for updating your email address</h2>
		<p>An email confirming your request has been sent to <b>${email}</b>.</p>
		<p>Please follow the directions in your confirmation email to complete the update process.</p>
                <p>You are now logged out, and you must confirm the new email account before continuing.</p>
                <p>If you have made a mistake, you can log back in and you will have enough limited access to
                   change your email address again.</p>
            </div>
        </td>
    </body>
</html>
