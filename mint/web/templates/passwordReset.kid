<?xml version='1.0' encoding='UTF-8'?>

<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Password Reset</a>
    </div>
    <head>
        <title>${formatTitle('Password Reset')}</title>
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>Your password has been reset.</h2>
		<p>An email with a new password has been sent to <b>${email}</b>.</p>
            </div>
        </td>
    </body>
</html>
