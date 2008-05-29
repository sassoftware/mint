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
                addOutboundMirror_setUseReleases(${kwargs['useReleases']});
                connect('mirrorByGroup', 'onclick', addOutboundMirror_onMirrorByGroup);
                connect('mirrorByLabel', 'onclick', addOutboundMirror_onMirrorByGroup);
                connect('useReleases', 'onclick', addOutboundMirror_onUseReleases);
                connect('useLabels', 'onclick', addOutboundMirror_onUseReleases);

            });
        </script>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/processEditOutbound" method="post">
                <input type="hidden" name="id" value="${id}" />
                <h2 py:if="id == -1">Add Outbound Mirror</h2>
                <h2 py:if="id != -1">Edit Outbound Mirror</h2>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th style="width: 1%;"><em py:strip="not isNew" class="required">${projectText().title()} to mirror:</em></th>
                        <td>
                            <select id="projectId" name="projectId">
                                <option value="-1">--</option>
                                <option py:attrs="{'selected': kwargs['projectId'] == project[0] and 'selected' or None}"
                                        py:for="project in projects" value="${project[0]}">${project[2]}</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">Update Services:</em></th>
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
                        <th><em class="required">Method:</em></th>
                        <td>
                            <p class="help notopmargin">
                                Select a method by which appliances will be
                                mirrored.  Release-based publishing is the
                                preferred method, as it will mirror precisely
                                the groups from which you have built images.
                                Label-based mirroring is also available for
                                backwards compatibility and for certain
                                scenarios in which it is more applicable.
                            </p>
                            <ul class="plainlist indent">
                                <li><label>
                                    <input py:attrs="{'checked': kwargs['useReleases'] and 'checked' or None}" class="radio" type="radio"
                                        name="useReleases" id="useReleases" value="1" />
                                    Mirror published releases
                                </label></li>
                                <li><label>
                                    <input py:attrs="{'checked': not kwargs['useReleases'] and 'checked' or None}" class="radio" type="radio"
                                        name="useReleases" id="useLabels" value="0" />
                                    Mirror labels
                                </label></li>
                            </ul>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">Labels:</em></th>
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
                        <th><em class="required">Groups:</em></th>
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
                        <th>Options:</th>
                        <td>
                            <input py:attrs="{'checked': kwargs['mirrorSources'] and 'checked' or None,
                                              'disabled': (kwargs['useReleases'] or (kwargs['mirrorBy'] == 'group')) and 'disabled' or ''}"
                                   class="check" type="checkbox" name="mirrorSources" value="1" id="mirrorSources" />
                            <label for="mirrorSources">Include source components when mirroring (only valid when mirroring by label)</label>
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
