<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Manage Jobs')}</title>
    </head>
    <body onload="javascript:listActiveJobs(false);">
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
              <h2>Manage Jobs</h2>
              <h3>Current Job Server Status</h3>
              <p>${jobServerStatus}</p>
              <form action="${cfg.basePath}admin/jobserverOperation" method="post">
                  <button py:if="enableToggle" name="operation" value="start">Start Job Server</button>
                  <button py:if="enableToggle" name="operation" value="stop">Stop Job Server</button>
              </form>
              <p id="jobsTable">Retrieving job status from server...</p>
        </div>
    </body>
</html>
