<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Legal Information')}</title>
    </head>
    <body id="legal">
      <center>
        <h2>Legal Information</h2>

        <p><a href="${cfg.basePath}legal?page=tos">Terms of Service</a></p>

        <p><a href="${cfg.basePath}legal?page=privacy">Privacy Policy</a></p>

        <p>rPath, the rPath logo, Conary, and rBuilder are
        trademarks of rPath, Inc.</p>

        <p>All other trademarks referenced are the property of their
        respective owners.</p>
      </center>
    </body>
</html>
