<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.web.templatesupport import projectText
    from rpath_common.proddef import api1 as proddef
    for var in [ 'name',
                 'description' ]:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title py:if="isNew">${formatTitle('Create New %s Version'%projectText().title())}</title>
        <div py:if="not isNew">
            <title py:if="kwargs.has_key('linked')">${formatTitle('Update Initial %s Version'%projectText().title())}</title>
            <title py:if="not kwargs.has_key('linked')">${formatTitle('Edit %s Version'%projectText().title())}</title>
        </div>
        <style>
            <![CDATA[
            a:hover.pdusource-adder,
            a:hover.pdusource-deleter,
            a:hover.pdbuilddef-adder,
            a:hover.pdbuilddef-expander,
            a:hover.pdbuilddef-deleter {
                color: inherit;
                background-color: inherit;
                cursor: pointer;
            }
            ]]>
        </style>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/tables.css?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/editversion.js?v=${cacheFakeoutVersion}"/>
    </head>
    <body>
        <div py:def="buildDefinitionOptions(valueToTemplateIdMap, visibleBuildTypes, ordinal='bt', bdef=None)" py:strip="True">
            <?python
                from mint import buildtypes
                from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE
                if bdef:
                    imageType = bdef.getBuildImageType()
                    buildType = buildtypes.xmlTagNameImageTypeMap.get(imageType.tag)
                    buildSettings = imageType.fields
                    buildName = bdef.getBuildName()
                    buildBaseFlavor = bdef.getBuildBaseFlavor()
                else:
                    buildType = visibleBuildTypes[0]
                    buildSettings = {}
                    buildName = 'NEWBUILD'
                    buildBaseFlavor = ''
            ?>
            <tr id="pdbuilddef-${ordinal}">
                <td>
                    <input type="text" name="pdbuilddef-${ordinal}-name" value="${buildName}" />
                </td>
                <td>
                    <select class="pdbuilddef-picker-buildType" name="pdbuilddef-${ordinal}-_buildType">
                        <option py:for="key in visibleBuildTypes"
                            py:attrs="{'value': key, 'selected': (buildType == key) and 'selected' or None}"
                            py:content="buildtypes.typeNames[key]" />
                    </select>
                </td>
                <td>
                    <div py:strip="True" py:for="key in visibleBuildTypes">
                        <?python
                            elementClasses = 'arch-%d' % key
                            elementName = 'pdbuilddef-%s-baseFlavor' % (ordinal)
                            elementId = 'pdbuilddef-buildtype%s-%s-baseFlavor' % (key, ordinal)

                            # get the supported arch types for this build type
                            if buildtypes.buildDefinitionSupportedFlavorsMap.has_key(key):
                                suppArchTypes = dict()
                                typesList = buildtypes.buildDefinitionSupportedFlavorsMap[key]
                                for type in typesList:
                                    suppArchTypes[type] = buildtypes.buildDefinitionFlavorMap[type]
                            else:
                                # not in the map, so allow all
                                suppArchTypes = buildtypes.buildDefinitionFlavorMap

                            elementDisabled = buildType != key and 'disabled' or None
                            elementStyle = buildType != key and 'display: none' or None

                            # get a default flavor to work with in case build type hasn't been set
                            # this is just the first value in the supported archs dict
                            defaultVal = suppArchTypes and suppArchTypes.values()[0] or ''
                        ?>
                        <select py:attrs="{'id': elementId, 'name': elementName, 'disabled': elementDisabled}" style="${elementStyle}" class="${elementClasses}">
                            <option py:for="v in sorted(suppArchTypes)"
                                py:attrs="{'value': buildtypes.buildDefinitionFlavorMap[v],
                                           'selected': ((buildBaseFlavor or defaultVal) == buildtypes.buildDefinitionFlavorMap[v]) and 'selected' or None}"
                                py:content="buildtypes.buildDefinitionFlavorNameMap[v]" />
                        </select>
                    </div>
                </td>
                <td class="row-button"><a class="pdbuilddef-expander"><img src="${cfg.staticPath}/apps/mint/images/icon_edit.gif" title="Edit" /></a></td>
                <td class="row-button"><a class="pdbuilddef-deleter"><img src="${cfg.staticPath}/apps/mint/images/icon_delete.gif" title="Delete" /></a></td>
            </tr>
            <tr id="pdbuilddef-${ordinal}-more" style="display: none">
                <td colspan="5">
                    <fieldset>
                        <legend>Build Definition Settings</legend>
                        <div py:strip="True" py:for="name, data in valueToTemplateIdMap.items()">
                        <?python
                            validFor, dataRow = data
                            elementClasses = ' '.join(['it-%d' % x for x in validFor])       
                            dataValue = buildSettings.get(name, dataRow[1])
                            elementName = 'pdbuilddef-%s-%s' % (ordinal, name)
                            elementDisabled = buildType not in validFor and 'disabled' or None
                            elementStyle    = buildType not in validFor and 'display: none' or None
                        ?>
                        <div py:if="(dataRow[0] == RDT_BOOL)" style="${elementStyle}" class="${elementClasses}">
                            <input py:attrs="{'class': 'reversed',
                                              'id': elementName,
                                              'type': 'checkbox',
                                              'checked': (dataValue) and 'checked' or None,
                                              'name': elementName,
                                              'value': 'True',
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
                                              'class': (dataRow[0] == RDT_STRING) and 'field-text-string' or 'field-text-int',
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
        
        <div py:def="upstreamSourcesOptions(ordinal='bt')" py:strip="True">
            <tr id="pdusource-${ordinal}">
                <td>
                    <input type="text" name="pdusource-${ordinal}-package" value="foo 1 package" />
                </td>
                <td>
                    <input type="text" name="pdusource-${ordinal}-label" value="foo1 label" />
                </td>
                <td class="row-button"><a class="pdusource-deleter"><img src="${cfg.staticPath}/apps/mint/images/icon_delete.gif" title="Delete" /></a></td>
            </tr>
        </div>
        
        <div py:def="releaseStagesOptions(relstage=None, ordinal='bt')" py:strip="True">
            <?python
                relstageName = relstage and relstage.name or ''
                relstageLabelSuffix = relstage and relstage.labelSuffix or ''
            ?>
            <tr id="pdstages-${ordinal}">
                <!--!
                   We add labels and hidden fields so the user can not edit
                   the stages.  This will need to be changed when the stages
                   can be edited.  i.e. remove the labels and make the hidden
                   fields text fields.
                -->
                <td>
                    <label for="pdstages-${ordinal}-name" py:content="relstageName" />
                    <input type="hidden" name="pdstages-${ordinal}-name" value="${relstageName}"/>
                </td>
                <td>
                    <label for="pdstages-${ordinal}-labelSuffix" py:content="relstageLabelSuffix" />
                    <input type="hidden" name="pdstages-${ordinal}-labelSuffix" value="${relstageLabelSuffix}"/>
                </td>
            </tr>
        </div>

        <div id="layout">
            <h2 py:if="isNew">Create New ${projectText().title()} Version</h2>
            <div py:if="not isNew">
                <!--!
                If kwargs['linked'] exists, we were sent here after creating a 
                new product.  Set the title appropriately.
                -->
                <h2 py:if="not kwargs.has_key('linked')">Edit ${projectText().title()} Version</h2>
                <h2 py:if="kwargs.has_key('linked')">Update Initial ${projectText().title()} Version</h2>
            </div>
            <p py:if="kwargs.has_key('linked')">
                <!--!
                If kwargs['linked'] exists, we were sent here after creating a 
                new product.  Add the transitional help text.
                -->
                Next enter the additional data necessary to define version
                '${kwargs['name']}' of your ${projectText().lower()}.
            </p>
            <!--! Only new ones have a required field for now -->
            <p py:if="isNew">Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form method="post" action="processEditVersion">
                <table border="0" cellspacing="0" cellpadding="0"
                    class="mainformhorizontal">
                    <tr>
                        <th>
                            <!--! version only required if creating new one -->
                            <div py:if="not isNew">Version:</div>
                            <em py:if="isNew" class="required">Version:</em>
                        </th>
                        <td py:if="isNew">
                            <input type="text" autocomplete="off" name="name"
                                value="${kwargs['name']}"/>
                            <p class="help">
                                Choose an initial version for your ${projectText().lower()}. Versions may contain
                                any combination of alphanumeric characters and decimals but
                                cannot contain any spaces (for example, '1', 'A', '1.0', '2007' are
                                all legal versions, but '1.0 XL' is not).
                            </p>
                        </td>
                        <td py:if="not isNew">${kwargs['name']}<input type="hidden" name="name" value="${kwargs['name']}" /></td>
                    </tr>
                    <tr>
                        <th>Version Description:</th>
                        <td>
                            <textarea rows="6" cols="72" name="description"
                                py:content="kwargs['description']"></textarea>
                            <p class="help">Please provide a description of
                                this version of your ${projectText().lower()}.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>Release Stages:</th>
                        <td>
                            <table id="pdstages" class="pretty-fullwidth">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Label Suffix</th>
                                        <th>&nbsp;</th>
                                        <th>&nbsp;</th>
                                        <th>&nbsp;</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <div py:strip="True" py:for="ordinal, relstage in enumerate(productDefinition.getStages())"
                                         py:content="releaseStagesOptions(relstage, ordinal)" />
                                     <tr id="pdstages-empty" py:attrs="{'style': productDefinition.getStages() and 'display: none;' or None}">
                                        <td colspan="4">No release stages defined.</td>
                                    </tr>
                                </tbody>
                            </table>
                            <table id="pdstages-bt-all" style="display: none">
                                <tbody py:content="releaseStagesOptions()" />
                            </table>
                        </td>
                    </tr>
                    <!--  Upstream Sources currently disabled -->
                    <tr py:if="False">
                        <th>Upstream Sources:</th>
                        <td>
                            <table id="pdusource" class="pretty-fullwidth">
                                <thead>
                                    <tr>
                                        <th>Project</th>
                                        <th>Version</th>
                                        <th>&nbsp;</th>
                                        <th>&nbsp;</th>
                                        <th>&nbsp;</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <div py:strip="True" py:for="us in kwargs['upstreamSources']"
                                         py:content="upstreamSourcesOptions()" />
                                     <tr id="pdusource-empty" py:attrs="{'style': len(kwargs['upstreamSources']) and 'display: none;' or None}">
                                        <td colspan="4">No upstream sources defined.</td>
                                    </tr>
                                </tbody>
                            </table>
                            <table id="pdusource-bt-all" style="display: none">
                                <tbody py:content="upstreamSourcesOptions()" />
                            </table>
                            <p>
                                <a class="pdusource-adder">
                                    <img src="${cfg.staticPath}/apps/mint/images/icon_add.gif" title="Add" />
                                    Add a new upstream source
                                </a>
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <th>Build Definitions:</th>
                        <td>
                            <table id="pdbuilddefs" class="pretty-fullwidth">
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
                                    <div py:strip="True" py:for="ordinal, bdef in enumerate(productDefinition.getBuildDefinitions())"
                                         py:content="buildDefinitionOptions(buildTemplateValueToIdMap, visibleBuildTypes, ordinal, bdef)" />
                                     <tr id="pdbuilddef-empty" py:attrs="{'style':productDefinition.getBuildDefinitions() and 'display: none;' or None}">
                                        <td colspan="5">No builds defined.</td>
                                    </tr>
                                </tbody>
                            </table>
                            <table id="pdbuilddef-bt-all" style="display: none">
                                <tbody py:content="buildDefinitionOptions(buildTemplateValueToIdMap, visibleBuildTypes)" />
                            </table>
                            <p><a class="pdbuilddef-adder"><img src="${cfg.staticPath}/apps/mint/images/icon_add.gif" title="Add" />Add a new build definition</a></p>
                        </td>
                    </tr>
                </table>
                <p>
                    <button class="img" type="submit">
                        <div py:if="kwargs.has_key('linked')">
                            <!--! 
                            Always use create button if coming from create a product page
                            -->
                            <img src="${cfg.staticPath}/apps/mint/images/create_button.png" title="Create" />
                        </div>
                        <div py:if="not kwargs.has_key('linked')">
                            <img py:if="isNew" src="${cfg.staticPath}/apps/mint/images/create_button.png" title="Create" />
                            <img py:if="not isNew" src="${cfg.staticPath}/apps/mint/images/submit_button.png" title="Submit" />
                        </div>
                    </button>
                </p>
                <input type="hidden" name="id" value="${id}" />
                <input py:if="kwargs.has_key('linked')" type="hidden" name="linked" value="${kwargs['linked']}" />
            </form>
        </div>
    </body>
</html>
