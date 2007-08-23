<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <!--
         Copyright (c) 2005-2007 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Job Control Console</title>
        <link type="text/css" href="${tg.url('/mcpconsole/static/css/mcp.css')}"
            rel="stylesheet" media="screen" />
        <meta http-equiv="refresh" content="15" />
        <script type="text/javascript" src="${tg.url('/mcpconsole/static/javascript/mcpconsole.js')}"></script>
    </head>

    <?python
        from raa.widgets.tabbedpage import TabbedPageWidget
        from rPath.mcpconsole.templates import pageList

        from mcp import jobstatus
    ?>

    <body id="middleWide">
        ${TabbedPageWidget(forcepage='index').display(pageList)}
        <table py:if="not disabled" class="mcpJobs" cellspacing="0">
            <thead>
                <tr>
                    <th />
                    <th>Job ID</th>
                    <th>Status</th>
                    <th width="40" />
                </tr>
            </thead>
            <tbody id="jobs">
                <div py:for="id, info in jobStatus" py:strip="True">
                    <?python status = jobstatus.statusNames[info['status'][0]] ?>
                    <tr class="mcpJobSummary mcpJobColor${status}">
                        <td onclick="doHide(this)">+</td>
                        <td><b>${id}</b></td>
                        <td>${status}</td>
                        <td>
                          <form action="killJob" method="POST" py:if="jobstatus.FINISHED > info['status'][0]">
                            <input type="hidden" name="jobId" value="${id}"/>
                            <button type="submit">Kill</button>
                          </form>
                        </td>
                    </tr>
                    <tr class="mcpJobDetails mcpJobColor${status}">
                        <td colspan="4" class="hidden">
                          <ul class="jobEntry">
                            <li><b>jobId:</b> ${id}</li>
                            <li><b>Status:</b> ${status}</li>
                            <li><b>Message:</b> ${info['status'][1]}</li>
                            <li py:if="info['slaveId']"><b>Slave ID:</b> ${info['slaveId']}</li>
                          </ul>
                        </td>
                    </tr>
                </div>
            </tbody>
        </table>
        <div py:if="disabled">
            <h3>MCP Console is disabled</h3>
            Unable to contact the MCP
        </div>
    </body>
</html>
