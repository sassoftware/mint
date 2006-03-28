<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('View Reports')}</title>
    </head>
    <body>
	<a href ="${cfg.basePath}administer">Return to Administrator Page</a>
        <td id="main" class="spanall">
            <div class="pad">
              <form action="${cfg.basePath}administer" method="post">
                <h2>Select a report</h2>
                <p>
                  <select name="reportName">
                    <option py:for="report in availableReports" value="${report[0]}" py:content="report[1]"/>
                  </select>
                </p>
                <p>
                  <button name="operation" value="report_view">View Report</button>
                </p>
              </form>
            </div>
        </td>
    </body>
</html>
