<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

    <head>
        <title>${formatTitle('Edit rMake Build')}</title>
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/rmakebuilder.js"/>
    </head>
    <body>
        <div id="layout">
            <?python
                from mint.web.templatesupport import dictToJS
                from rmake.build import buildjob, buildtrove
                jobStatusCodes = {buildjob.STATE_FAILED:   'statusError',
                                  buildjob.STATE_BUILT: 'statusFinished'}
                trvStatusCodes = {buildtrove.TROVE_STATE_FAILED: 'statusError',
                                  buildtrove.TROVE_STATE_BUILT:  'statusFinished'}
            ?>
            <div id="right" class="side">
                ${resourcePane()}
            </div>

            <div id="spanleft" py:if="rMakeBuild.status==buildjob.STATE_INIT">
                This job has not been sent to rMake yet.
            </div>
            <div id="spanleft" py:if="rMakeBuild.status!=buildjob.STATE_INIT">
                <script type="text/javascript">
                <![CDATA[
                    trvStatusCodes = ${dictToJS(trvStatusCodes)};
                    jobStatusCodes = ${dictToJS(jobStatusCodes)};
                    stopStatusList = ${str([buildjob.STATE_FAILED, buildjob.STATE_BUILT])};
                    addLoadEvent(initrMakeManager(${rMakeBuild.id}));
                ]]>
                </script>
                <h3 id="rmakebuilder-jobid">rMake Job ID: ${rMakeBuild.jobId or 'Unknown'}</h3>
                <div id="rmakebuilder-status" class="${jobStatusCodes.get(rMakeBuild.status, 'statusRunning')}">
                    ${rMakeBuild.statusMessage}
                </div>
                <table>
                    <tr py:for="trvDict in troveList">
                        <td>${trvDict['trvName']}: </td>
                        <td id="rmakebuilder-item-status-${trvDict['rMakeBuildItemId']}" class="${trvStatusCodes.get(trvDict['status'], 'statusRunning')}" width="100%">
                            ${trvDict['statusMessage']}
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    </body>
</html>
