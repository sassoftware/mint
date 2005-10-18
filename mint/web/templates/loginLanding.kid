<?xml version='1.0' encoding='UTF-8'?>

<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Logged In')}</title>
        <meta http-equiv="refresh" content="0;url=$to" />
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>Thank you for logging in.</h2>

                <p>You will be redirected immediately. If you aren't: <a href="${cfg.basePath}">Continue</a></p>
            </div>
        </td>
    </body>
</html>
