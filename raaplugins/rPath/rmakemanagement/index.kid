<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> 

<?python
import raa.templates.master
from raa.web import makeUrl, getConfigValue, inWizardMode
from rPath import rmakemanagement
from rPath.rmakemanagement import pageList
?>

<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
      py:extends="raa.templates.master">

<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->    

<head>
    <title>${getConfigValue('product.productName')}: rMake Management</title>

    <script type="text/javascript">
    //addLoadEvent(rAPA.RoundedButton.init);

    function doAct(service, action, msg)
    {
        var p = new Post('changeServerState', ['service', 'action'], [service, action]);
        var d = p.doAction();
        d = d.addCallback(reloadNoHistory);
    }

    function doReset(service, msg)
    {
        var p = new Post('resetServer', [], []);
        var d = p.doAction();
        d = d.addCallback(reloadNoHistory);
    }

    function toggleBuildLog(link, expand, collapse, buildId) {
        var el = $(buildId);
        if(null == el) {
            return;
        }
        if(link.src.match("expand")) {
            link.src = collapse;
            el.style.display = '';
            normal = collapse;
            hover = collapse_h;
            readLog(buildId)
        } else {
            link.src = expand;
            el.style.display = 'none';
            normal = expand;
            hover = expand_h;
        }
    }

    function toggleEditNode(link, show, edit_node) {
        var el = $(edit_node);
        if(null == el) {
            return;
        }
        if(show == '1') {
            el.style.display = '';
        } else {
            el.style.display = 'none';
        }
    }

    function scrollToBottom()
    {
        var viewer = $("viewer");
        viewer.scrollTop = viewer.scrollHeight;
    }

    function readLog(buildId)
    {
        var d = new Post('getBuildLog', ['buildId'], [buildId]).doAction();
        d = d.addCallback(callbackGetLogData, buildId);
    }

    function callbackGetLogData(buildId, req){
        var logData = req.logText;
        var viewer = $("viewer-" + buildId);
        viewer.value = logData;
        scrollToBottom();
        return req;
    }

    function editNode(node, slots, chrootLimit){
        slots_el = $(slots)
        slots_v = slots_el.value
        chrootLimit_el = $(chrootLimit)
        chrootLimit_v = chrootLimit_el.value
        var p = new Post('editNode', ['node', 'slots', 'chrootLimit'], [node, slots_v, chrootLimit_v]);
        var d = p.doAction();
        d = d.addCallback(reloadNoHistory);
    }

    function postSave() {
        var url = 'saverMakeUserPass';
        var username = $('username').value;
        var password = $('password').value;
        var p =  new Post(url, ['username', 'password'], [username, password]);
        var d = p.doAction();
        d = d.addCallback(reloadNoHistory);
    }

    function postDelete() {
        var url = 'deleterMakeUserPass';
        var p =  new Post(url, [], []);
        var d = p.doAction();
        d = d.addCallback(reloadNoHistory);
    }
    </script>
</head>

<body>
    <?python
    instructions = "Use this page to manage the rMake server."
    start = makeUrl('/static/images/icon_start.gif')
    start_h = makeUrl('/static/images/icon_start_h.gif')
    stop = makeUrl('/static/images/icon_stop.gif')
    stop_h = makeUrl('/static/images/icon_stop_h.gif')
    restart = makeUrl('/static/images/icon_restart.gif')
    restart_h = makeUrl('/static/images/icon_restart_h.gif')
    expand_h = makeUrl('/static/images/icon_expand_h.gif');
    expand = makeUrl('/static/images/icon_expand.gif');
    collapse_h = makeUrl('/static/images/icon_collapse_h.gif');
    collapse = makeUrl('/static/images/icon_collapse.gif');
    edit_h = makeUrl('/static/images/icon_edit_h.gif')
    edit = makeUrl('/static/images/icon_edit.gif')
    ?>

    <div class="plugin-page" id="plugin-page">
        <div class="page-content">
            <div py:replace="display_instructions(instructions, raaInWizard)"> </div>

            <!--SERVER MANAGEMENT SECTION-->
            <div py:if="not inWizardMode()" py:strip="True">
            <div class="page-section">
            rMake Server Management
            </div>
            <div class="page-section-content">
                <table id="service-details">
                    <tr class="headers">
                        <td>rMake Server</td>
                        <td class="button-column">Status</td>
                        <td class="button-column">Start</td>
                        <td class="button-column">Stop</td>
                        <td class="button-column">Restart</td>
                        <td class="button-column">Reset</td>
                    </tr>

                    <form action="javascript:void(0);">
                        <div py:if="server is not None">
                            <tr>
                                <td>${server}</td>
                                <td class="button-column">${rmakemanagement.status.toString[status]}</td>
                                <td class="button-column service-action">
                                <input py:if="status != rmakemanagement.status.RUNNING" type="image" title="start" class="image" src="${start}" onclick="javascript:doAct('${rmakemanagement.rMakeServiceName}', '${rmakemanagement.action.START}', 'Starting ${rmakemanagement.rMakeServiceName} ...');" onMouseOver="this.src = '${start_h}'" onMouseOut="this.src = '${start}'"/>
                                <img py:if="status == rmakemanagement.status.RUNNING" type="image" title="start" src="${makeUrl('/static/images/icon_start_d.gif')}"/></td>
                                <td class="button-column service-action">
                                <input py:if="status != rmakemanagement.status.STOPPED" type="image" title="stop" class="image" src="${stop}" onclick="javascript:doAct('${rmakemanagement.rMakeServiceName}', '${rmakemanagement.action.STOP}', 'Stopping ${rmakemanagement.rMakeServiceName} ...');" onMouseOver="this.src = '${stop_h}'" onMouseOut="this.src = '${stop}'"/>
                                <img py:if="status == rmakemanagement.status.STOPPED" type="image" title="stop" src="${makeUrl('/static/images/icon_stop_d.gif')}"/></td>
                                <td class="button-column service-action">
                                <input py:if="status != rmakemanagement.status.STOPPED" type="image" title="restart" class="image" src="${restart}" onclick="javascript:doAct('${rmakemanagement.rMakeServiceName}', '${rmakemanagement.action.RESTART}', 'Restarting ${rmakemanagement.rMakeServiceName} ...');" onMouseOver="this.src = '${restart_h}'" onMouseOut="this.src = '${restart}'" />
                                <img py:if="status == rmakemanagement.status.STOPPED" type="image" title="restart" src="${makeUrl('/static/images/icon_restart_d.gif')}"/></td>
                                <td class="button-column service-action">
                                <input type="image" title="reset" class="image" src="${restart}" onclick="javascript:doReset('${rmakemanagement.rMakeServiceName}', 'Resetting ${rmakemanagement.rMakeServiceName} ...');" onMouseOver="this.src = '${restart_h}'" onMouseOut="this.src = '${restart}'" /></td>
                            </tr>
                        </div>
                        <div py:if="server is None">
                        </div>
                    </form>
                </table>
            </div>
            </div>

            <!--NODE SECTION-->
            <div py:if="len(nodes) > 0" py:strip="True">
            <div class="page-section">rMake Node Management</div>
            <div class="page-section-content">
                <table id="service-details">
                    <tr class="headers">
                        <td>rMake Node</td>
                        <td class="button-column">Status</td>
                        <td class="button-column">Start</td>
                        <td class="button-column">Stop</td>
                        <td class="button-column">Restart</td>
                        <td class="button-column">Reset</td>
                        <td class="button-column">Edit</td>
                    </tr>
                    <form action="javascript:void(0);">
                        <div py:for="node in nodes">
                            <tr>
                                <td>${node}</td>
                                <td class="button-column">${rmakemanagement.status.toString[nodes[node]['status']]}</td>
                                <td class="button-column service-action">
                                <input py:if="nodes[node]['status'] != rmakemanagement.status.RUNNING" type="image" title="start" class="image" src="${start}" onclick="javascript:doAct('${rmakemanagement.nodeServiceName}', '${rmakemanagement.action.START}', 'Starting ${rmakemanagement.nodeServiceName} ...');" onMouseOver="this.src = '${start_h}'" onMouseOut="this.src = '${start}'"/>
                                <img py:if="nodes[node]['status'] == rmakemanagement.status.RUNNING" type="image" title="start" src="${makeUrl('/static/images/icon_start_d.gif')}"/></td>
                                <td class="button-column service-action">
                                <input py:if="nodes[node]['status'] != rmakemanagement.status.STOPPED" type="image" title="stop" class="image" src="${stop}" onclick="javascript:doAct('${rmakemanagement.nodeServiceName}', '${rmakemanagement.action.STOP}', 'Stopping ${rmakemanagement.nodeServiceName} ...');" onMouseOver="this.src = '${stop_h}'" onMouseOut="this.src = '${stop}'"/>
                                <img py:if="nodes[node]['status'] == rmakemanagement.status.STOPPED" type="image" title="stop" src="${makeUrl('/static/images/icon_stop_d.gif')}"/></td>
                                <td class="button-column service-action">
                                <input py:if="nodes[node]['status'] != rmakemanagement.status.STOPPED" type="image" title="restart" class="image" src="${restart}" onclick="javascript:doAct('${rmakemanagement.nodeServiceName}', '${rmakemanagement.action.RESTART}', 'Restarting ${rmakemanagement.nodeServiceName} ...');" onMouseOver="this.src = '${restart_h}'" onMouseOut="this.src = '${restart}'" />
                                <img py:if="nodes[node]['status'] == rmakemanagement.status.STOPPED" type="image" title="restart" src="${makeUrl('/static/images/icon_restart_d.gif')}"/></td>
                                <td class="button-column service-action">
                                <input type="image" title="reset" class="image" src="${restart}" onclick="javascript:doAct('${rmakemanagement.nodeServiceName}', '${rmakemanagement.action.RESTART}', 'Resetting ${rmakemanagement.nodeServiceName} ...');" onMouseOver="this.src = '${restart_h}'" onMouseOut="this.src = '${restart}'" /></td>
                                <td class="button-column service-action">
                                <input type="image" title="edit" class="image" src="${edit}" onclick="javascript:toggleEditNode(this, '1','edit_${node[0]}')" onMouseOver="this.src = '${edit_h}'" onMouseOut="this.src = '${edit}'" /></td>
                            </tr>

                            <tr id='edit_${node[0]}' style="display: none;">
                            <td colspan="7" align="right">
                            <table>
                                <tr>
                                    <td colspan="2">Enter the slots and chrootLimit for this node.</td>
                                </tr>
                                <tr>
                                    <td>Slots:</td>
                                    <td>
                                        <input type="text" id="slots" name="slots" value="${nodes[node]['slots']}"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td>chrootLimit:</td>
                                    <td>
                                        <input type="text" id="chrootLimit" name="chrootLimit" value="${nodes[node]['chrootLimit']}"/>
                                    </td>
                                </tr>
                                <tr>
                                    <td class="form-buttons">
                                    <a class="rnd_button panel float-right" href="javascript:editNode('${node}', 'slots', 'chrootLimit');">Save</a>
                                    </td>
                                    <td class="form-buttons">
                                    <a class="rnd_button panel float-left" href="javascript:toggleEditNode(this, '0', 'edit_${node[0]}');">Cancel</a>
                                    </td>
                                </tr>
                            </table>
                            </td>
                            </tr>

                        </div>
                    </form>
                </table>
            </div>
            </div>

            <!--BUILD SECTION-->
            <div class="page-section">Builds</div>
            <div class="page-section-content">
                <table id="service-details">
                    <tr class="headers">
                        <td>Build Id</td>
                        <td>Trove Name</td>
                        <td>Status</td>
                        <td>Completed Time</td>
                        <td class="button-column">View build log</td>
                    </tr>
                    <div py:if="builds" py:strip="True" py:for="build in builds">
                        <tr> 
                            <td><span class="emphasis">${build[0]}</span></td>
                            <td>${build[1]}</td>
                            <td>${build[2]}</td>
                            <td py:if="build[3]">${build[4]}</td>
                            <td py:if="not build[3]"></td>
                            <td class="button-column">
                            <img src="${makeUrl('/static/images/icon_expand.gif')}" onclick="javascript:toggleBuildLog(this, expand, collapse, '${build[0]}')" style="cursor: pointer; vertical-align: text-top; padding-right: 4px;" onMouseOver="this.src = this.src.match('expand') ? expand_h : collapse_h" onMouseOut="this.src = this.src.match('expand') ? expand : collapse"/>
                            </td>
                        </tr>
                        <tr id="${build[0]}" style="display: none; background: #f8f8f8;">
                            <td colspan="4">
                                <div id="log-console">
                                    <textarea readonly="True" class="console" id="viewer-${build[0]}"></textarea>
                                </div>
                            </td>
                        </tr>
                    </div>
                    <div py:if="not builds" py:strip="True">
                        <tr>
                        <td>${statusmsg}</td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        </tr>
                    </div>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
