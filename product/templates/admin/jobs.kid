<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="administer?operation=jobs">Manage Jobs</a>
    </div>

    <head>
        <title>${formatTitle('Manage Jobs')}</title>
    </head>
    <body onload="javascript:listActiveJobs(false);">
        <div class="layout">
            <div class="pad">
              <p py:if="kwargs.get('extraMsg', None)" class="message" py:content="kwargs['extraMsg']"/>
              <h1>Manage Jobs</h1>
              <p id="jobsTable">Retrieving job status from server...</p>
              <form action="administer" method="post">
                  <h2>Current Job Server Status</h2>
                  <p>${jobServerStatus}</p>
                  <button py:if="enableToggle" name="operation" value="jobs_jobserver_start">Start Job Server</button>
                  <button py:if="enableToggle" name="operation" value="jobs_jobserver_stop">Stop Job Server</button>
              </form>
              <p><a href ="${cfg.basePath}administer/">Return to Administrator Page</a></p>
            </div>
        </div>
    </body>
</html>
