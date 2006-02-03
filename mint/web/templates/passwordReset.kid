<?xml version='1.0' encoding='UTF-8'?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Password Reset')}</title>
    </head>
    <body>
        <div id="layout">
            <h2>Your password has been reset.</h2>
            <p>An email with a new password has been sent to <strong>${email}</strong>.</p>
        </div>
    </body>
</html>
