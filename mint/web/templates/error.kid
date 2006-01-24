<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Error')}</title>
    </head>
    <body>
        <div class="layout">
            <p class="error">Error:</p>
            <p class="errormessage">${error}</p>
            <p>
                Please go back and try again or contact
                ${XML(cfg.supportContactHTML)}
                for assistance.
            </p>
        </div>
    </body>
</html>
