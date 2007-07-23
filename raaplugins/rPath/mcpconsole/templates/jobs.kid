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
        <meta http-equiv="refresh" content="5"/>
    </head>

    <?python
        from raa.widgets.tabbedpage import TabbedPageWidget
        from rPath.mcpconsole.templates import pageList

        from mcp import jobstatus
    ?>

    <body id="middleWide">
        ${TabbedPageWidget(forcepage='index').display(pageList)}
        <div py:if="not disabled">
            <h3>Jobs:</h3>
            <ul class="jobSection">
                <li py:for="id, info in jobStatus.iteritems()">
                    <dl class="jobEntry">
                        <dt>jobId</dt>
                            <dd>${id}</dd>
                        <dt>Status</dt>
                            <dd>${jobstatus.statusNames[info['status'][0]]}</dd>
                        <dt>Message</dt>
                            <dd>${info['status'][1]}</dd>
                        <div py:if="info['slaveId']" py:strip="True">
                        <dt>Slave ID</dt>
                            <dd>${info['slaveId']}</dd>
                        </div>
                    </dl>
                    <form action="killJob" method="POST" py:if="jobstatus.FINISHED > info['status'][0]">
                        <input type="hidden" name="jobId" value="${id}"/>
                        <button type="submit">Kill</button>
                    </form>
                </li>
            </ul>
        </div>
        <div py:if="disabled">
            <h3>MCP Console is disabled</h3>
            Unable to contact the MCP
        </div>
    </body>
</html>
