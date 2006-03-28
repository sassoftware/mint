<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Manage Jobs')}</title>
    </head>
    <body onload="javascript:listActiveJobs(false);">
        <div class="layout">
            <div class="pad">
              <p py:if="kwargs.get('extraMsg', None)" class="message" py:content="kwargs['extraMsg']"/>
              <h1>Manage Jobs</h1>
              <p id="jobsTable">Retrieving job status from server...</p>
              <p><a href ="${cfg.basePath}administer/">Return to Administrator Page</a></p>
            </div>
        </div>
    </body>
</html>
