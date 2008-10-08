<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python 
import raa.templates.master
import raa.web
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <!--
         Copyright (c) 2005-2008 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Job Control Console</title>
        <link type="text/css" href="${raa.web.makeUrl('/mcpconsole/static/css/mcp.css')}" rel="stylesheet" media="screen" />
        <meta http-equiv="refresh" content="15" />
        <script type="text/javascript" src="${raa.web.makeUrl('/mcpconsole/static/javascript/mcpconsole.js')}"></script>
    </head>

    <?python
        from raa.templates.tabbedpagewidget import TabbedPageWidget
        from rPath.mcpconsole.templates import pageList
        from mcp import jobstatus
        import re
    ?>

    <body>
        <div class="plugin-page" id="plugin-page">
            <div class="page-content">
            ${TabbedPageWidget(forcepage='index', value=pageList)}

            <div class="page-section">

            <div py:if="not disabled">
                <h3>Current Jobs</h3>
                <div class="mcpJobs">
                    <table>
                        <thead>
                            <tr class="tableHeadings">
                                <th>Job ID</th>
                                <th>Origin</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>&nbsp;</th>
                            </tr>
                        </thead>
                        <tbody id="jobs">
                            <div py:for="id, info in jobStatus" py:strip="True">
                                <?python
                                    status = jobstatus.statusNames[info['status'][0]]
                                    match = re.search('^(.*)-(build|cook)-(\d+-\d+)$', id)
                                    if not match:
                                        # Doesnt have a build count, e.g. with pre-release rbuilder 4.x
                                        match = re.search('^(.*)-(build|cook)-(\d+)$', id)
                                    if match:
                                        jobOrigin, jobType, jobId = match.groups()
                                    else:
                                        # Dont know what this is...
                                        jobOrigin, jobType, jobId = "unknown", "unknown", "unknown"
                                ?>
                                <tr class="mcpJobSummary mcpJobColor${status}">
                                    <td py:content="jobId" />
                                    <td py:content="jobOrigin" />
                                    <td py:content="jobType" />
                                        <td>${status} <span py:if="status == 'Running'" py:content="'[%s]' % info['slaveId']" py:strip="True" />
                                        <div class="jobMessage" py:if="status == 'Running'" py:content="info['status'][1]"/>
                                    </td>
                                    <td class="actionButton">
                                        <form action="killJob" method="POST" py:if="jobstatus.FINISHED > info['status'][0]">
                                            <input type="hidden" name="jobId" value="${id}"/>
                                            <button type="submit">Kill</button>
                                        </form>
                                    </td>
                                </tr>
                            </div>
                        </tbody>
                    </table>
                </div>
            </div>

            <div py:if="disabled">
                <h3>MCP Console is disabled</h3>
                Unable to contact the MCP
            </div>

            </div>
            </div>

        </div>
    </body>
</html>
