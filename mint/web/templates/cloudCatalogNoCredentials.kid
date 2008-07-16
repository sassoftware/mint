<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('rBuilder Catalog for EC2(TM) - Need Credentials')}</title>
    </head>
    <body>
        <div id="layout">
            <div style="width: 100%; height: 400px; text-align: center">
                <h1>Before You Begin...</h1>
                <p>rBuilder Catalog for EC2&trade; requires that your user account has valid
                    credentials for Amazon Web Services&trade;.</p>
                <p>Please <a href="http://${SITE}cloudSettings">click here to setup your credentials</a>.</p>
                <p>Alternatively, you may <a href="http://${SITE}">return to ${cfg.productName}</a>.</p>
            </div>
        </div>
    </body>
</html>
