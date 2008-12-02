<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('View Reports')}</title>
    </head>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
              <form action="${cfg.basePath}admin/viewReport" method="post">
                <div class="page-title-no-project">Select a Report</div>
                <p>
                  <select name="reportName">
                    <option py:for="report in availableReports" value="${report[0]}" py:content="report[1]"/>
                  </select>
                </p>
                 <br />
                <p>
                  <button type="submit">View Report</button>
                </p>
                 <br />
              </form>
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
