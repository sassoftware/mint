<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
<!--
 Copyright (c) 2005 rPath, Inc.

 All Rights Reserved
-->
    <head>
        <title>${formatTitle('Repository Notice')}</title>
    </head>
    <body>
        <div id="inner">
            <h2>Notice</h2>

            <p>${message}</p>
            <p>Return to <a href="${url}">${link}</a></p>
        </div>
    </body>
</html>
