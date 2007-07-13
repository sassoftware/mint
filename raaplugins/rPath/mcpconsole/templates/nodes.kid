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

        from mcp import slavestatus
        slaveStatusCss = {slavestatus.IDLE :    'idleSlave',
                          slavestatus.BUILDING: 'buildingSlave',
                          slavestatus.ACTIVE:   'runningSlave',
                          slavestatus.OFFLINE:  'offlineSlave',
                          None:                 'unknownSlave'}
    ?>

    <body id="middleWide">
        ${TabbedPageWidget().display(pageList)}
        <div py:if="disabled == False">
            <h3>Job Masters:</h3>
            <ul>
            <li py:for="id, info in sorted(nodeStatus.iteritems())" class="jobMaster">
               <strong>${id}</strong>:
               ${info['arch']}
               <ul>
	           <li py:for="slaveId, data in sorted(info['slaves'].iteritems())" class="jobSlave ${slaveStatusCss.get(data['status'], 'unknownSlave')}">

                       <dl py:if="data">
                           <dt>slaveName</dt>
                               <dd>${slaveId.split(':')[-1]}</dd>
                           <dt>status</dt>
                               <dd>${slavestatus.statusNames.get(data['status'])}</dd>
                           <dt>type</dt>
                               <dd>${data['type']}</dd>
                           <dt>jobId</dt>
                               <dd>${str(data['jobId'])}</dd>
                       </dl>
                       <form action="stopSlave" method="POST">
                            <input type="hidden" name="slaveId" value="${slaveId}"/>
                            <input type="hidden" name="delayed" value="0"/>
                            <button type="submit">Kill</button>
                        </form>
                       <form action="stopSlave" method="POST">
                            <input type="hidden" name="slaveId" value="${slaveId}"/>
                            <input type="hidden" name="delayed" value="1"/>
                            <button type="submit">Stop</button>
                        </form>
                   </li>
                   <li py:for="x in range(info['limit'] - len(info['slaves']))" class="jobSlave offlineSlave"/>
               </ul>
               <form action="setSlaveLimit" method="POST">
                   <input type="hidden" name="masterId" value="${id}"/>
                   <input type="text" name="limit"/>
                   <button type="submit">Limit</button>
               </form>
            </li>
            </ul>
        </div>
        <div py:if="disabled == True">
            <h3>MCP Console is disabled</h3>
            Unable to contact the MCP
        </div>
    </body>
</html>
