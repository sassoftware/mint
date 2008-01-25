<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.web.templatesupport import projectText
?>

    <head>
        <title>${formatTitle('Add Outbound Mirror')}</title>
        <script type="text/javascript">
            addLoadEvent(function(){
                getGroups(getElement('projectId').value,
                    function() { setSelectedGroups(${kwargs['selectedGroups']});});
                getProjectLabels(getElement('projectId').value,
                    function(){ setSelectedLabels(${kwargs['selectedLabels']});});
                connect('projectId', 'onchange', addOutboundMirror_onProjectChange);
            });
        </script>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/processAddOutbound" method="post">
                <input type="hidden" name="id" value="${id}" />
                <h2>Add Outbound Mirror</h2>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th style="width: 1%;"><em class="required">${projectText().title()} to mirror:</em></th>
                        <td>
                            <select id="projectId" name="projectId">
                                <option value="-1">--</option>
                                <option py:attrs="{'selected': kwargs['projectId'] == project[0] and 'selected' or None}"
                                        py:for="project in projects" value="${project[0]}">${project[2]}</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">Labels:</em></th>
                        <td>
                            <input py:attrs="{'checked': kwargs['allLabels'] and 'checked' or None}" class="radio" type="radio" name="allLabels" value="1" id="allLabels" />
                            <label for="allLabels">Mirror all labels</label><br />
                            <select style="float: right; vertical-align: top; width: 20em; height: 10em;" id="labelList" name="labelList" multiple="multiple" />
                            <input py:attrs="{'checked': not kwargs['allLabels'] and 'checked' or None}" class="radio" type="radio" name="allLabels" value="0" id="selectLabels" />
                            <label for="selectLabels">Mirror only selected labels</label>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">Groups:</em></th>
                        <td>
                            <input py:attrs="{'checked': (kwargs['mirrorBy'] == 'label') and 'checked' or None}" class="radio" type="radio" name="mirrorBy" value="label" id="mirrorByLabel" />
                            <label for="mirrorByLabel">Mirror all contents</label><br />
                            <select style="float: right; vertical-align: top; width: 20em; height: 10em;" multiple="multiple" name="groups" id="groups" />
                            <input py:attrs="{'checked': (kwargs['mirrorBy'] == 'group') and 'checked' or None}" class="radio" type="radio" name="mirrorBy" value="group" id="mirrorByGroup" />
                            <label for="mirrorByGroup">Mirror groups and their referenced packages</label>
                        </td>
                    </tr>
                    <tr>
                        <th>Options:</th>
                        <td>
                            <input py:attrs="{'checked': kwargs['mirrorSources'] and 'checked' or None}"
                                   class="check" type="checkbox" name="mirrorSources" value="1" id="mirrorSources" />
                            <label for="mirrorSources">Include source components when mirroring</label>
                        </td>
                    </tr>
                </table>
                <input type="submit" id="submitButton" name="action"
                    value="${(id == -1) and 'Save' or 'Update'}"
                       py:attrs="{'disabled': (id == -1) and 'disabled' or None}" />
                <input type="submit" name="action" value="Cancel" />
            </form>
            <div>&nbsp;</div>
        </div>
    </body>
</html>
