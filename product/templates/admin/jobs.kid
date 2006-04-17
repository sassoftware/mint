<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="${cfg.basePath}admin/jobs">Manage Jobs</a>
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
              <form action="${cfg.basePath}admin/jobserverOperation" method="post">
                  <h2>Current Job Server Status</h2>
                  <p>${jobServerStatus}</p>
                  <button py:if="enableToggle" name="operation" value="start">Start Job Server</button>
                  <button py:if="enableToggle" name="operation" value="stop">Stop Job Server</button>
              </form>
              <p><a href ="${cfg.basePath}admin/">Return to Administrator Page</a></p>
            </div>
        </div>
    </body>
</html>
