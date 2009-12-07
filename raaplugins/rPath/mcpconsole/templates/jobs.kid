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

    <div py:def="doLoad(a, b, c)" py:strip="True">
      ${'%.02f' % a} &bull; ${'%.02f' % b} &bull; ${'%.02f' % c}
    </div>

    <div py:def="jobList(jobs, nonemsg)" py:strip="True">
      <ul py:if="len(jobs) > 0" class="jobList">
        <li py:for="job in jobs">
          <a href="killJob?jobId=${job.uuid}" class="killButton">stop</a>
          ${job.uuid}
        </li>
      </ul>
      <div py:if="len(jobs) == 0" class="jobList">$nonemsg</div>
    </div>

    <body>
        <div class="plugin-page" id="plugin-page"><div class="page-content">

            <div py:if="not disabled" class="page-section">
              <div py:for="n, node in enumerate(nodes)" class="jobMaster">
                <form action="setSlaveLimit" method="POST" name="node_$n">
                  <input type="hidden" name="masterId" value="${node.session_id}"/>
                  <h4>Node: ${node.session_id}</h4>
                  <ul class="nodeStatus">
                    <li>Load average: ${doLoad(*node.machine_info.loadavg)}</li>
                    <li>Slots: <input name="limit" size="2" value="${node.slots}"/></li>
                  </ul>
                  <h5>Running Jobs</h5>
                  ${jobList(node.jobs, "No jobs are running.")}
                  <a class="rnd_button node-button" href="javascript:button_submit(document.node_$n)">Save</a>
                  <div class="clear-right" />
                </form>
              </div>

              <div class="queuedJobs">
                <h4>Queued Jobs</h4>
                ${jobList(queued, "No jobs are queued.")}
              </div>

            </div>

            <div py:if="disabled">
                <h3>MCP Console is disabled</h3>
                Unable to contact the MCP
            </div>

        </div></div>
    </body>
</html>
