<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python 
import raa.templates.master
import raa.web
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <!--
         Copyright (c) 2005-2007 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title>Job Control Console</title>
        <link type="text/css" href="${raa.web.makeUrl('/mcpconsole/static/css/mcp.css')}"
            rel="stylesheet" media="screen" />
        <meta http-equiv="refresh" content="5"/>
    </head>

    <?python
        from raa.templates.tabbedpagewidget import TabbedPageWidget
        from rPath.mcpconsole.templates import pageList

        from mcp import slavestatus
        slaveStatusCss = {slavestatus.IDLE :    'idleSlave',
                          slavestatus.BUILDING: 'buildingSlave',
                          slavestatus.ACTIVE:   'runningSlave',
                          slavestatus.OFFLINE:  'offlineSlave',
                          None:                 'unknownSlave'}
    ?>

    <body>
        <div class="plugin-page" id="plugin-page">
            <div class="page-content">
            ${TabbedPageWidget(value=pageList)}
            <div class="page-section">

            <div py:if="not disabled">
                <h3>Job Master Nodes</h3>
                <div py:for="id, info in sorted(nodeStatus.iteritems())" class="jobMaster">
                    <table>
                        <thead>
                            <tr>
                                <th colspan="5">${id} (${info['arch']})</th>
                            </tr>
                            <tr class="tableHeadings">
                                <th>Slave Id</th>
                                <th>Version (arch)</th>
                                <th>Status</th>
                                <th>Job Id</th>
                                <th>&nbsp;</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr py:for="slaveId, data in sorted(info['slaves'].iteritems())" class="jobSlave ${slaveStatusCss.get(data['status'], 'unknownSlave')}">
                                <div py:if="data" py:strip="True">
                                    <?python slaveVer, slaveArch = data['type'].split(':') ?>
                                    <td py:content="slaveId.split(':')[-1]" />
                                    <td py:content="'%s (%s)' % (slaveVer, slaveArch)" />
                                    <td py:content="slavestatus.statusNames.get(data['status'])" />
                                    <td py:content="str(data['jobId'])" />
                                    <td class="actionButton">
                                        <form action="stopSlave" method="POST">
                                            <input type="hidden" name="slaveId" value="${slaveId}" />
                                            <button type="submit">Kill</button>
                                        </form>
                                    </td>
                                </div>
                            </tr>
                            <div py:if="info.get('limit')" strip="True">
                                <tr py:for="x in range(info['limit'] - len(info['slaves']))" class="jobSlave offlineSlave">
                                    <td colspan="5">[ Empty Slot ]</td>
                                </tr>
                            </div>
                        </tbody>
                    </table>
                    <div class="jobMasterSettings">
                        <form action="setSlaveLimit" method="POST">
                            <input type="hidden" name="masterId" value="${id}"/>
                            <label for="jobMasterLimit_${id}">Maximum number of job slaves:</label>
                            <input id="jobMasterLimit_${id}" type="text" name="limit" size="2" value="${info.get('limit','')}" />
                            <button type="submit">Limit</button>
                        </form>
                    </div>
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
