<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('View Reports')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
          <form action="${cfg.basePath}admin/viewReport" method="post">
            <h2>Select a report</h2>
            <p>
              <select name="reportName">
                <option py:for="report in availableReports" value="${report[0]}" py:content="report[1]"/>
              </select>
            </p>
            <p>
              <button type="submit">View Report</button>
            </p>
          </form>
        </div>
    </body>
</html>
