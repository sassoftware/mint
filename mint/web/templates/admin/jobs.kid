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
              <!-- COMING SOON ... <h2>Other Job Tasks</h2>
              <form action="administer" method="post">
                  <button name="operation" value="jobs_toggle_jobserver">Start / Stop Job Server</button>
              </form> -->
              <p><a href ="/administer/">Return to Administrator Page</a></p>
            </div>
        </div>
    </body>
</html>
