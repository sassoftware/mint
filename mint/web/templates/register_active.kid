<?xml version='1.0' encoding='UTF-8'?>

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Account Confirmed')}</title>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${stepsWidget(['Get Started', 'Sign Up', 'Confirm Email'], 3)}
            </div>
            <div id="spanleft">
                <h2>Thank you for confirming</h2>
                <p>Your account has now been confirmed.</p>
                <p>Please <a href="${cfg.basePath}">sign in</a> to begin using ${cfg.productName}.</p>
            </div>
        </div>
    </body>
</html>
