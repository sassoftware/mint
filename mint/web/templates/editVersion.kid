<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
    for var in [ 'name',
                 'description',
                 'buildDefinitions',
                 'upstreamSources'
                 'stages',
                 'visibleBuildTypes',
                 'buildTemplateValueToIdMap',
                ]:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title py:if="isNew">${formatTitle('Create New Product Version')}</title>
        <title py:if="not isNew">${formatTitle('Edit Product Version')}</title>
        <style>
            <![CDATA[
            table#pd-builddefs {
                border-collapse: collapse;
                width: 100%;
            }

            a:hover.pd-builddef-adder,
            a:hover.pd-builddef-expander,
            a:hover.pd-builddef-deleter {
                color: inherit;
                background-color: inherit;
                cursor: pointer;
            }

            table#pd-builddefs tr td {
                font-size: x-small;
            }

            table#pd-builddefs tr th,
            table#pd-builddefs tr td {
                padding: 4px 4px;
                border-bottom: 1px solid #e0e0e0;
            }

            table#pd-builddefs tr.pd-builddef-expanded td,
            table#pd-builddefs tr.pd-builddef-more td {
                background: #fffded;
                border-bottom: none;
            }

            table#pd-builddefs tr.pd-builddef-more td {
                border-bottom: 1px solid #e0e0e0;
            }

            table#pd-builddefs th {
                font-size: normal;
                font-weight: bold;
                background-color: #ccc;
                color: #000;
            }

            table#pd-builddefs tr td input {
                width: 100%;
            }

            table#pd-builddefs tr td label {
                text-align: right;
                width: 30%;
                margin-left: 10px;
                padding-right: 10px;
            }

            table#pd-builddefs tr td label.reversed {
                text-align: left;
                width: 65%;
                padding-left: 5px;
                padding-right: 0;
            }

            table#pd-builddefs tr td input.reversed {
                width: 14px;
                margin-left: 30px;
            }

            table#pd-builddefs input.field,
            table#pd-builddefs select.field {
                width: auto;
            }

            table.row-button {
                width: 20px;
            }
            ]]>
        </style>
        <script type="text/javascript">
            <![CDATA[
                var currentSerial = 0;

                jQuery(document).ready(function () {

                currentSerial = jQuery(".pd-builddef-deleter").length;

                jQuery('select.pd-builddef-picker-buildType').change(function() {
                    var builddefElement = jQuery(this).parents('tr').get(0);
                    var builddefmoreElement= jQuery(builddefElement).next().get(0);
                    var buildtype = this.value;
                    var buildtypeclass = '.it-'+buildtype;

                    jQuery(builddefmoreElement).find('div.it-'+buildtype).each(function () {
                        jQuery(this).show();
                        jQuery(this).find(':input').removeAttr('disabled');
                    });
                    jQuery(builddefmoreElement).find('div:not(.it-'+buildtype+')').each(function () {
                        if (jQuery(this).is(':not(.clearleft)')) {
                            jQuery(this).hide();
                        }
                        jQuery(this).find(':input').attr('disabled', 'disabled');
                    });
                });

                jQuery('.pd-builddef-adder,.pd-builddef-expander,.pd-builddef-deleter').hover(function () {
                        var imgbutton = jQuery(this).find('img').get(0);
                        imgbutton.src = imgbutton.src.replace('.gif', '_h.gif');
                    }, function() {
                        var imgbutton = jQuery(this).find('img').get(0);
                        imgbutton.src = imgbutton.src.replace('_h.gif', '.gif');
                });

                jQuery('.pd-builddef-expander').click(function () {
                        var imgbutton = jQuery(this).find('img').get(0);
                        var builddefId = "#" + jQuery(this).parents().get(1).id;
                        var builddefmoreId = builddefId + "-more";
                        if (jQuery(builddefId).attr('class') == 'pd-builddef-expanded') {
                            jQuery(builddefmoreId).hide();
                            jQuery(builddefId).removeAttr('class');
                            jQuery(builddefmoreId).removeAttr('class');
                        } else {
                            jQuery(builddefmoreId).show();
                            jQuery(builddefId).attr('class', 'pd-builddef-expanded');
                            jQuery(builddefmoreId).attr('class', 'pd-builddef-more');
                        }
                });

                jQuery('.pd-builddef-deleter').click(function () {
                        var builddefId = "#" + jQuery(this).parents().get(1).id;
                        var builddefmoreId = builddefId + '-more';
                        jQuery(builddefId).remove();
                        jQuery(builddefmoreId).remove();
                });

                jQuery('.pd-builddef-adder').click(function () {
                    currentSerial++;
                    var templateDomBits = jQuery('#pd-builddef-bt-all > tbody').clone(true);
                    templateDomBits.find(':disabled').removeAttr('disabled');
                    templateDomBits.find('label').each(function () {
                        this.htmlFor = this.htmlFor.replace('bt', String(currentSerial));
                    });
                    templateDomBits.find('input,select').each(function () {
                        if (this.id) { this.id = this.id.replace('bt', String(currentSerial)); }
                        if (this.name) { this.name = this.name.replace('bt', String(currentSerial)); }
                    });
                    templateDomBits.find('tr').each(function () {
                        if (this.id) { this.id = this.id.replace('bt', String(currentSerial)); }
                    });
                    templateDomBits.find('select').change();
                    templateDomBits.find('.pd-builddef-expander').click();
                });
            });
            ]]>
        </script>
    </head>
    <body>
        <div py:def="buildDefinitionOptions(valueToTemplateIdMap, visibleBuildTypes, ordinal='bt', bdef={})" py:strip="True">
            <?python
                from mint import buildtypes
                from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE
                buildType = bdef.get('buildType', 1)
            ?>
            <tr id="pd-builddef-${ordinal}">
                <td>
                    <input type="text" name="pd-builddef-${ordinal}-name" value="${bdef.get('name','')}" />
                </td>
                <td>
                    <select class="pd-builddef-picker-buildType" name="pd-builddef-${ordinal}-buildType">
                        <option py:for="key in visibleBuildTypes"
                            py:attrs="{'value': key, 'selected': (bdef.get('buildType', visibleBuildTypes[0]) == key) and 'selected' or None}"
                            py:content="buildtypes.typeNames[key]" />
                    </select>
                </td>
                <td>
                    <select id="pd-builddef-picker-baseFlavorType" name="pd-builddef-${ordinal}-baseFlavorType">
                        <option py:for="v in sorted(buildtypes.buildDefinitionFlavorTypes.values())"
                            py:attrs="{'value': buildtypes.buildDefinitionFlavorMap[v],
                                       'selected': (bdef.get('baseFlavor', '') == buildtypes.buildDefinitionFlavorMap[v]) and 'selected' or None}"
                            py:content="buildtypes.buildDefinitionFlavorNameMap[v]" />
                    </select>
                </td>
                <td class="row-button"><a class="pd-builddef-expander"><img src="${cfg.staticPath}/apps/mint/images/icon_edit.gif" alt="edit" /></a></td>
                <td class="row-button"><a class="pd-builddef-deleter"><img src="${cfg.staticPath}/apps/mint/images/icon_delete.gif" alt="delete" /></a></td>
            </tr>
            <tr id="pd-builddef-${ordinal}-more" style="display: none">
                <td colspan="5">
                    <fieldset>
                        <legend>Build Definition Settings</legend>
                        <div py:strip="True" py:for="name, data in valueToTemplateIdMap.items()">
                        <?python
                            validFor, dataRow = data
                            elementClasses = ' '.join(['it-%d' % x for x in validFor])
                            dataValue = bdef.get(name, dataRow[1])
                            elementName = 'pd-builddef-%s-%s' % (ordinal, name)
                            elementDisabled = buildType not in validFor and 'disabled' or None
                            elementStyle    = buildType not in validFor and 'display: none' or None
                        ?>
                        <div py:if="(dataRow[0] == RDT_BOOL)" style="${elementStyle}" class="${elementClasses}">
                            <input py:attrs="{'class': 'reversed',
                                              'id': elementName,
                                              'type': 'checkbox',
                                              'checked': 'checked' and dataValue or None,
                                              'name': elementName,
                                              'value': '1',
                                              'class': 'check field',
                                              'disabled': elementDisabled}" />
                            <label class="reversed" for="${elementName}" py:content="dataRow[2]" />
                            <div class="clearleft">&nbsp;</div> 
                        </div>
                        <div py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)" style="${elementStyle}" class="${elementClasses}">
                            <label for="${elementName}" py:content="dataRow[2]" />
                            <input py:attrs="{'id': elementName,
                                              'type': 'text',
                                              'name': elementName,
                                              'value': dataValue,
                                              'class': 'field',
                                              'disabled': elementDisabled}" />
                            <div class="clearleft">&nbsp;</div>
                        </div>
                        <div py:if="(dataRow[0] == RDT_ENUM)" style="${elementStyle}" class="${elementClasses}">
                            <label for="${elementName}" py:content="dataRow[2]" />
                            <select py:attrs="{'id': elementName,
                                               'name': elementName,
                                               'class': 'field',
                                               'disabled': elementDisabled}">
                                <option py:for="prompt, val in sorted(dataRow[3].iteritems())"
                                    py:content="prompt" value="${val}"
                                    py:attrs="{'selected' : val == dataValue and 'selected' or None}" />
                            </select>
                            <div class="clearleft">&nbsp;</div> 
                        </div>
                    </div>
                    </fieldset>
                </td>
            </tr>
        </div>

        <div id="layout">
            <h2 py:if="isNew">Create New Product Version</h2>
            <h2 py:if="not isNew">Edit Product Version</h2>
            <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form method="post" action="processEditVersion">
                <table border="0" cellspacing="0" cellpadding="0"
                    class="mainformhorizontal">
                    <tr>
                        <th>
                            <em class="required">Version Name</em>
                        </th>
                        <td py:if="isNew">
                            <input type="text" autocomplete="off" name="title"
                                value="${kwargs['name']}"/>
                            <p class="help">Choose a major version number
                                for your product. Versions may contain alphanumeric
                                characters and decimals but may not contain any spaces
                                (e.g. '1', 'A', '1.0', '2007' are all legal versions,
                                but '1.0 XL' is not).</p>
                        </td>
                        <td py:if="not isNew" py:content="kwargs['name']" />
                    </tr>
                    <tr>
                        <th>Version Description:</th>
                        <td>
                            <textarea rows="6" cols="72" name="description"
                                py:content="kwargs['description']"></textarea>
                            <p class="help">Please provide a description of
                                this version of your product.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>Release Stages:</th>
                        <td>
                            <table id="relstages">
                                <tr>
                                    <th>Name</th>
                                    <th>Description</th>
                                    <th>Tag Suffix</th>
                                </tr>
                                <tr py:for="relstage in kwargs['stages']">
                                    <td py:content="relstage[0]" />
                                    <td py:content="relstage[1]" />
                                    <td py:content="relstage[2]" />
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <th>Upstream Sources:</th>
                        <td>
                            <table id="usources">
                                <tr>
                                    <th>Package</th>
                                    <th>Label</th>
                                    <th>Edit</th>
                                    <th>Delete</th>
                                </tr>
                                <tr id="usource-template" style="display:none">
                                    <td colspan="4">
                                        <label for="custom-usource-label">Repository Label</label>
                                        <input name="custom-usource-label" value="" type="text" /><br />
                                        <input type="radio" id="custom-usource-all" name="custom-usource-all" value="1" checked="checked" />
                                        <label for="custom-usource-all">All Packages</label><br />
                                        <input type="radio" id="custom-usource-notall" name="custom-usource-all" value="0" checked="" />
                                        <label for="custom-usource-notall">Specific Package or Group</label>
                                        <input type="text" id="custom-usource-trovename" name="custom-usource-name" value="" />
                                    </td>
                                </tr>
                                <tr py:if="not len(kwargs['upstreamSources'])">
                                    <td colspan="4">No upstream sources defined.</td>
                                </tr>
                                <tr py:for="us in kwargs['upstreamSources']">
                                    <td py:content="us[0]" />
                                    <td py:content="us[1]" />
                                    <td>[edit]</td>
                                    <td>[delete]</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <th>Build Definitions:</th>
                        <td>
                            <table id="pd-builddefs">
                                <thead>
                                    <tr>
                                        <th class="builddef-name">Name</th>
                                        <th>Build Type</th>
                                        <th>Architecture</th>
                                        <th>&nbsp;</th>
                                        <th>&nbsp;</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <div py:strip="True" py:for="ordinal, bdef in enumerate(kwargs['buildDefinitions'])"
                                         py:content="buildDefinitionOptions(kwargs['buildTemplateValueToIdMap'], kwargs['visibleBuildTypes'], ordinal, bdef)" />
                                    <tr id="pd-builddef-empty" py:attrs="{'style': kwargs['buildDefinitions'] and None or 'display: none'}">
                                        <td colspan="5">No builds defined.</td>
                                    </tr>
                                </tbody>
                            </table>
                            <table id="pd-builddef-bt-all" style="display: none">
                                <tbody py:content="buildDefinitionOptions(kwargs['buildTemplateValueToIdMap'], kwargs['visibleBuildTypes'])" />
                            </table>
                            <p><a class="pd-builddef-adder"><img src="${cfg.staticPath}/apps/mint/images/icon_add.gif" alt="Add" />Add a new build definition</a></p>
                        </td>
                    </tr>
                </table>
                <p>
                    <input id="submitButton" type="submit" name="action" value="Submit" />
                    <input type="submit" name="action" value="Cancel" />
                </p>
                <input type="hidden" name="id" value="${id}" />
            </form>
        </div>
    </body>
</html>
