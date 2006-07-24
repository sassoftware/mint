<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('rMake Build Status')}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/rmakebuilder.js"/>
    </head>
    <body>
        <div id="layout">
            <?python
                from mint.web.templatesupport import dictToJS
                from mint.rmakeconstants import buildjob, buildtrove
                jobStatusCodes = {buildjob.JOB_STATE_FAILED:   'statusError',
                                  buildjob.JOB_STATE_BUILT: 'statusFinished',
                                  buildjob.JOB_STATE_COMMITTED : 'statusFinished'}
                trvStatusCodes = {buildtrove.TROVE_STATE_FAILED: 'statusError',
                                  buildtrove.TROVE_STATE_BUILT:  'statusFinished'}
            ?>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="spanleft" py:if="rMakeBuild.status==buildjob.JOB_STATE_INIT">
                This job has not been sent to rMake yet.
            </div>
            <div id="spanleft" py:if="rMakeBuild.status!=buildjob.JOB_STATE_INIT">
                <?python
                    commitFailed = rMakeBuild.statusMessage.startswith('Commit failed')
                ?>
                <script type="text/javascript">
                <![CDATA[
                    trvStatusCodes = ${dictToJS(trvStatusCodes)};
                    jobStatusCodes = ${dictToJS(jobStatusCodes)};
                    stopStatusList = ${str([buildjob.JOB_STATE_FAILED, buildjob.JOB_STATE_BUILT, buildjob.JOB_STATE_COMMITTED])};
                    buildjob = ${str(buildjob)};
                    buildtrove = ${str(buildtrove)};
                    addLoadEvent(function () {initrMakeManager(${rMakeBuild.id})});
                    addLoadEvent(function() {roundElement('statusAreaHeader', {'corners': 'tl tr'})});
                ]]>
                </script>
                <table>
                    <tr>
                        <td>
                            <span id="rmakebuilder-jobid">
                                rMake Job ID: ${rMakeBuild.jobId or 'Unknown'}
                            </span>
                        </td>
                        <td>
                            <span>
                                ${rMakeBuildNextAction(troveList)}
                            </span>
                        </td>
                    </tr>
                </table>
                ${statusArea("rMake Build")}
                <table>
                    <tr py:for="trvDict in troveList">
                        <td>${trvDict['trvName']}: </td>
                        <td id="rmakebuilder-item-status-${trvDict['rMakeBuildItemId']}" class="${trvStatusCodes.get(commitFailed and buildtrove.TROVE_STATE_FAILED or trvDict['status'], 'statusRunning')}" width="100%">
                            ${trvDict['statusMessage']}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </body>
</html>
