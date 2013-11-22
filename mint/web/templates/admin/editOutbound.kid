<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
#
# Copyright (c) SAS Institute Inc.
#
-->
<?python
    from mint.web.templatesupport import projectText
    from mint import helperfuncs
?>

    <head>
        <title py:if="id == -1">${formatTitle('Add Outbound Mirror')}</title>
        <title py:if="id != -1">${formatTitle('Edit Outbound Mirror')}</title>
        <script type="text/javascript">
            addLoadEvent(function(){
                getGroups(getElement('projectId').value,
                     ${kwargs['selectedGroups']});
                getProjectLabels(getElement('projectId').value,
                    ${kwargs['selectedLabels']});
                connect('projectId', 'onchange', addOutboundMirror_onProjectChange);
                connect('mirrorByGroup', 'onclick', addOutboundMirror_onMirrorByGroup);
                connect('mirrorByLabel', 'onclick', addOutboundMirror_onMirrorByGroup);
            });
        </script>
    </head>
    <body>
    <div class="admin-page">
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="admin-spanright">
            <form action="${cfg.basePath}admin/processEditOutbound" method="post">
                <input type="hidden" name="id" value="${id}" />
                <div class="page-title-no-project" py:if="id == -1">Add Outbound Mirror</div>
                <div class="page-title-no-project" py:if="id != -1">Edit Outbound Mirror</div>

                <table class="mainformhorizontal">
                <tr>
                    <td class="form-label"><em py:strip="not isNew" class="required">${projectText().title()} to mirror:</em></td>
                    <td>
                        <select id="projectId" name="projectId" style="width:auto;">
                            <option value="-1">--</option>
                            <option py:attrs="{'selected': kwargs['projectId'] == project[0] and 'selected' or None}"
                                    py:for="project in projects" value="${project[0]}">${project[2]}</option>
                        </select>
                    </td>
                </tr>
                <tr>
                    <td class="form-label"><em class="required">Update Services:</em></td>
                    <td>
                        <p py:if="kwargs['allTargets']" class="help notopmargin">
                            Choose one or more Update Services
                            to publish the content for this project.
                        </p>
                        <ul class="plainlist indent">
                            <li py:for="upsrvId, hostname, _, _, description in kwargs['allTargets']"><label>
                                <input id="upsrv_${upsrvId}" name="selectedTargets" class="check" type="checkbox" value="${upsrvId}"
                                    py:attrs="{'checked': (upsrvId in kwargs['selectedTargets']) and 'checked' or None}" />
                                ${hostname}
                                <span py:strip="True" py:if="description"> (${helperfuncs.truncateForDisplay(description)})</span>
                            </label></li>
                        </ul>
                        <div class="help" py:if="not kwargs['allTargets']">
                            No Update Services have been configured for this
                            instance of ${cfg.productName}. You may still
                            configure outbound mirroring for this
                            ${projectText()}, but be aware that packages
                            will not be published until
                            <ol>
                                <li>rBuilder is configured for one or more
                                    Update Services, and</li>
                                <li>Each ${projectText()}'s outbound
                                    mirroring setup has
                                    had one or more of the Update
                                    Services added to its configuration.</li>
                            </ol>
                        </div>
                    </td>
                </tr>
                <tr>
                    <td class="form-label"><em class="required">Labels:</em></td>
                    <td>
                        <p class="help notopmargin">
                            You may choose to publish content from all of the
                            labels on your ${projectText()}'s repository,
                            or you may choose to restrict publishing content
                            to one or more labels.
                        </p>
                        <ul class="plainlist indent">
                            <li><label>
                                <input name="allLabels" id="allLabels" value="1" class="radio" type="radio"
                                    py:attrs="{'checked': kwargs['allLabels'] and 'checked' or None}" />
                                Mirror all labels
                            </label></li>
                            <li><label>
                                <input name="allLabels" id="selectLabels" value="0" class="radio" type="radio"
                                    py:attrs="{'checked': not kwargs['allLabels'] and 'checked' or None}" />
                                Mirror only selected labels
                            </label></li>
                        </ul>
                        <div id="chklist_labelList" />
                    </td>
                </tr>
                <tr>
                    <td class="form-label"><em class="required">Groups:</em></td>
                    <td>
                        <p class="help notopmargin">
                            You may further restrict mirroring by choosing
                            to publish one or more groups. The publishing
                            process will publish all versions of each
                            group chosen including all of the packages
                            contained within the group.
                        </p>
                        <ul class="plainlist indent">
                            <li><label>
                                <input name="mirrorBy" id="mirrorByLabel" value="label" class="radio" type="radio"
                                    py:attrs="{'checked': (kwargs['mirrorBy'] == 'label') and 'checked' or None}" />
                                Mirror all contents
                            </label></li>
                            <li><label>
                                <input name="mirrorBy" id="mirrorByGroup" value="group" class="radio" type="radio"
                                    py:attrs="{'checked': (kwargs['mirrorBy'] == 'group') and 'checked' or None}" />
                                Mirror groups and their referenced packages
                            </label></li>
                        </ul>
                        <div id="chklist_groups" />
                    </td>
                </tr>
                <tr>
                    <td class="form-label">Options:</td>
                    <td>
                      <input py:attrs="{'checked': kwargs['mirrorSources'] and 'checked' or None}"
                               class="check" type="checkbox" name="mirrorSources" value="1" id="mirrorSources" />
                        <label for="mirrorSources">Include source components when mirroring (only valid when mirroring by label)</label>
                    </td>
                </tr>
                </table>
                <br />
                <p class="p-button">
                <input type="submit" id="submitButton" name="action"
                    value="${(id == -1) and 'Save' or 'Update'}"
                       py:attrs="{'disabled': (id == -1) and 'disabled' or None}" />
                <input type="submit" name="action" value="Cancel" />
                </p>
                <br />
            </form>
            <div>&nbsp;</div>
        </div>
        <div class="bottom"/>
    </div>
    </body>
</html>
