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
    from mint.helperfuncs import truncateForDisplay, formatProductVersion
    from rpath_common.proddef import api1 as proddef
    for var in [ 'name',
                 'namespace',
                 'description' ]:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title py:if="isNew">${formatTitle('Create New %s Version'%projectText().title())}</title>
        <div py:if="not isNew" py:strip="True">
            <title py:if="kwargs.has_key('linked')">${formatTitle('Update Initial %s Version'%projectText().title())}</title>
            <title py:if="not kwargs.has_key('linked')">${formatTitle('Edit %s Version'%projectText().title())}</title>
        </div>
        
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/tables.css?v=${cacheFakeoutVersion}" />
        <script type="text/javascript" src="${cfg.staticPath}apps/mint/javascript/editversion.js?v=${cacheFakeoutVersion}"/>
        <script type="text/javascript">
        <![CDATA[
            function doSubmit() {
                var form = document.getElementById('processEditVersionForm');
                if(form) {
                   form.submit();
                }
            }
        
            function handleYes() {
                // they confirmed it, so move along
                doSubmit();
            }
            
            function handleNo() {
                // do nothing
            }
        
            function ensureBuildsDefined() {
               if(!buildsDefined) {
                  modalEditVersionWarning(handleYes, handleNo);
               } else {
                  doSubmit();
               }
            }
            ]]>
        </script>
    </head>
    <body>
                
        <div py:def="buildDefinitionOptions(valueToTemplateIdMap, visibleBuildTypes, ordinal='bt', bdef=None)" py:strip="True">
            <?python
                from mint import buildtypes
                from mint import buildtemplates
                from mint.data import RDT_STRING, RDT_BOOL, RDT_INT, RDT_ENUM, RDT_TROVE
                if bdef:
                    imageType = bdef.getBuildImageType()
                    buildType = buildtypes.xmlTagNameImageTypeMap.get(imageType.tag)
                    # Map XML names to optionNameMap
                    buildSettings = dict([(buildtemplates.optionNameMap.get(k,k),v) for k, v in imageType.fields.iteritems()])
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
                    <input type="text" name="pdbuilddef-${ordinal}-name" value="${buildName}" /></td>
                <td>
                    <select class="pdbuilddef-picker-buildType" name="pdbuilddef-${ordinal}-_buildType">
                        <option py:for="key in visibleBuildTypes"
                            py:attrs="{'value': key, 'selected': (buildType == key) and 'selected' or None}"
                            py:content="buildtypes.typeNames[key]" />
                    </select></td>
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

                            # get a default flavor to work with in case build type has not been set
                            # this is just the first value in the supported archs dict
                            defaultVal = suppArchTypes and suppArchTypes.values()[0] or ''
                        ?>
                        <select py:attrs="{'id': elementId, 'name': elementName, 'disabled': elementDisabled}" style="${elementStyle}" class="${elementClasses}">
                            <option py:for="v in sorted(suppArchTypes)"
                                py:attrs="{'value': buildtypes.buildDefinitionFlavorMap[v],
                                           'selected': ((buildBaseFlavor or defaultVal) == buildtypes.buildDefinitionFlavorMap[v]) and 'selected' or None}"
                                py:content="buildtypes.buildDefinitionFlavorNameMap[v]" />
                        </select>
                    </div></td>
                <td class="row-button"><a class="pdbuilddef-expander"><img src="${cfg.staticPath}/apps/mint/images/icon_edit-n.gif" title="Edit" /></a></td>
                <td class="row-button"><a class="pdbuilddef-deleter"><img src="${cfg.staticPath}/apps/mint/images/icon_delete-n.gif" title="Delete" /></a></td>
            </tr>
            <tr id="pdbuilddef-${ordinal}-more" style="display: none">
                <td class="image-edit-box" colspan="5">
                    <?python 
                        # save RDT classes to get proper display classes for example
                        troveElementBuildtypes = set()
                        # funky lambda is to sort by datatype ?>
                    <div py:strip="True" py:for="name, data in sorted(valueToTemplateIdMap.items(), key=lambda y: y[1][1][0])">
                    <?python
                        validFor, dataRow = data
                        elementClasses = ' '.join(['field-row'] + ['it-%d' % x for x in validFor])
                        if dataRow[0] == RDT_TROVE:
                            troveElementBuildtypes.update(set(validFor))
                        dataValue = buildSettings.get(name, dataRow[1])
                        elementName = 'pdbuilddef-%s-%s' % (ordinal, name)
                        elementDisabled = buildType not in validFor and 'disabled' or None
                        elementStyle    = buildType not in validFor and 'display: none' or None
                    ?>
                    <div py:if="(dataRow[0] == RDT_BOOL)" style="${elementStyle}" class="${elementClasses}">
                        <table class="check-table">
                            <tr>
                                <td>
                                <input py:attrs="{'id': elementName,
                                          'type': 'checkbox',
                                          'checked': (dataValue) and 'checked' or None,
                                          'name': elementName,
                                          'value': 'True',
                                          'class': 'check field',
                                          'disabled': elementDisabled}" /></td>
                                <td class="checkbox-label"><label for="${elementName}" py:content="dataRow[2]" /></td>
                            </tr>
                        </table>
                    </div>
                    <div py:if="(dataRow[0] == RDT_INT) or (dataRow[0] == RDT_STRING)" style="${elementStyle}" class="${elementClasses}">
                        <span class="label"><label for="${elementName}" py:content="dataRow[2]" />:</span><br />
                        <input py:attrs="{'id': elementName,
                                          'type': 'text',
                                          'name': elementName,
                                          'value': dataValue,
                                          'class': (dataRow[0] == RDT_STRING) and 'field-text-string' or 'field-text-int',
                                          'disabled': elementDisabled}" />
                        <br />
                    </div>
                    <div py:if="(dataRow[0] == RDT_ENUM)" style="${elementStyle}" class="${elementClasses}">
                        <span class="label"><label for="${elementName}" py:content="dataRow[2]" />:</span><br />
                        <select py:attrs="{'id': elementName,
                                           'name': elementName,
                                           'class': 'field',
                                           'disabled': elementDisabled}">
                            <option py:for="prompt, val in sorted(dataRow[3].iteritems())"
                                py:content="prompt" value="${val}"
                                py:attrs="{'selected' : val == str(dataValue) and 'selected' or None}" />
                        </select>
                        <br />
                    </div>
                    <div py:if="(dataRow[0] == RDT_TROVE)" style="${elementStyle}" class="${elementClasses}">
                        <span class="label"><label for="${elementName}" py:content="dataRow[2]" />:</span><br />
                        <input py:attrs="{'id': elementName,
                                          'type': 'text',
                                          'name': elementName,
                                          'value': dataValue,
                                          'class': 'field-text-string',
                                          'disabled': elementDisabled}" />
                        
                    </div>
                    </div>
                    <div py:attrs="{'class': ' '.join(['field-row', 'field-example'] + ['it-%d' % x for x in troveElementBuildtypes]),
                                        'style': buildType not in troveElementBuildtypes and 'display: none;' or ''}">
                        Special troves (e.g. anaconda-templates)
                        may be specified as labels or as specific versions. For example, using
                        <code>conary.rpath.com@rpl:1</code> will pick the latest trove from the
                        <code>conary.rpath.com@rpl:1</code> label, while using
                        <code>conary.rpath.com@rpl:1/1.0.8-0.1-3</code> will pick version
                        <code>1.0.8-0.1-3</code> from the
                        <code>conary.rpath.com@rpl:1</code> label.
                    </div>
                    
                </td>
            </tr>
        </div>
        
        <div py:def="upstreamSourcesOptions(usource=None, ordinal='bt')" py:strip="True">
        <?python
            if usource:
                troveName = usource.troveName or ''
                label = usource.label or ''
            else:
                troveName = ''
                label = ''
        ?>
            <tr id="pdusource-${ordinal}">
                <td>
                    <input type="text" name="pdusource-${ordinal}-troveName" value="${troveName}" />
                </td>
                <td>
                    <input type="text" name="pdusource-${ordinal}-label" value="${label}" />
                </td>
                <td class="row-button"><a class="pdusource-deleter"><img src="${cfg.staticPath}/apps/mint/images/icon_delete-n.gif" title="Delete" /></a></td>
            </tr>
        </div>
        
        <div py:def="releaseStagesOptions(relstage=None, ordinal='bt')" py:strip="True">
            <?python
                relstageName = relstage and relstage.name or ''
                relstageLabelSuffix = relstage and relstage.labelSuffix or ''
                labelSuffixDesc = relstageLabelSuffix and relstageLabelSuffix or '(no label suffix)'
            ?>
            <tr id="pdstages-${ordinal}">
                <!--!
                   We add labels and hidden fields so the user can not edit
                   the stages.  This will need to be changed when the stages
                   can be edited.  i.e. remove the labels and make the hidden
                   fields text fields.
                -->
                <td>
                    ${relstageName}
                    <input type="hidden" name="pdstages-${ordinal}-name" value="${relstageName}"/>
                </td>
                <td colspan="3">
                    ${labelSuffixDesc}
                    <input type="hidden" name="pdstages-${ordinal}-labelSuffix" value="${relstageLabelSuffix}"/>
                </td>
            </tr>
        </div>

        <div id="layout">

            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>
                <div id="middle">
                
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title" py:if="isNew">Create ${projectText().title()} Version</div>
                    <div py:if="not isNew">
                        <!--!
                        If kwargs['linked'] exists, we were sent here after creating a 
                        new product.  Set the title appropriately.
                        -->
                        <div class="page-title" py:if="not kwargs.has_key('linked')">Edit ${projectText().title()} Version</div>
                        <div class="page-title" py:if="kwargs.has_key('linked')">Update ${projectText().title()} Version</div>
                    </div>
                    <p py:if="kwargs.has_key('linked')">
                        <!--!
                        If kwargs['linked'] exists, we were sent here after creating a 
                        new product.  Add the transitional help text.
                        -->
                        Enter any additional data necessary to define version
                        '${kwargs['name']}' of your ${projectText().lower()}, including the images
                        you need to generate for this version.
                    </p>
                    <!--! Only new ones have a required field for now -->
                    <p py:if="isNew">Fields labeled with a <em class="required">red arrow</em> are required.</p>
                    <form method="post" id="processEditVersionForm" action="processEditVersion">
                    <table class="mainformhorizontal">
                    <tr>
                        <td class="form-label">
                            <em py:strip="not isNew" class="required">
                                Major Version:
                            </em>
                        </td>
                        <td py:if="isNew">
                            <input type="text" autocomplete="off" name="name"
                                value="${kwargs['name']}"/>
                            <p class="help">
                                Enter a ${projectText().lower()} Major Version that reflects the new major version of the
                                appliance ${projectText().lower()}.  This does not have to correspond to the version 
                                of the appliance software. Versions must start with an alphanumeric character
                                and may be followed by any other alphanumeric characters, separated if 
                                desired by decimals.  For example: '1', '1.0', '1.A', 'A1', and '2008' are all valid 
                                versions, but '2008 RC', '.', and '1.' are not valid.</p>
                        </td>
                        <td py:if="not isNew">${kwargs['name']}<input type="hidden" name="name" value="${kwargs['name']}" /></td>
                    </tr>
                    <tr py:if="availablePlatforms">
                        <td>
                            <em class="required" py:strip="not isNew">Appliance Platform:</em>
                        </td>
                        <td py:if="isNew">
                            <select name="platformLabel">
                                <option py:for="platformLabel, platformDesc in availablePlatforms" py:attrs="{'selected': (kwargs['platformLabel'] == platformLabel) and 'selected' or None}" value="${platformLabel}" py:content="platformDesc" />
                            </select>
                            <p class="help">Select a platform on which to base your appliance.</p>
                        </td>
                        <td py:if="not isNew">
                            ${platformName} <a py:if="not kwargs.has_key('linked')" class="option" href="rebaseProductVersion?id=${id}">update</a>
                            <p py:if="customPlatform">
                                This product version is based upon a custom
                                appliance platform.
                                <span py:if="not acceptablePlatform">
                                    ${cfg.productName} may have trouble building
                                    images and/or packages using this unknown
                                    appliance platform.
                                </span>
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label">Description:</td>
                        <td>
                            <textarea rows="4" cols="90" name="description" py:content="kwargs['description']"></textarea>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label">Release Stages:</td>
                        <td>
                            <table id="pdstages" class="pretty-fullwidth">
                            <thead>
                            <tr>
                                <th>Name</th>
                                <th>Label Suffix</th>
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
                            
                    <tr>
                        <td class="form-label">Image Set:</td>
                        <td>
                            <table id="pdbuilddefs" class="pretty-fullwidth">
                            <thead>
                            <tr>
                                <th class="builddef-name">Name</th>
                                <th>Image Type</th>
                                <th>Architecture</th>
                                <th>&nbsp;</th>
                                <th>&nbsp;</th>
                            </tr>
                            </thead>
                            <tbody>
                                <div py:strip="True" py:for="ordinal, bdef in enumerate(productDefinition.getBuildDefinitions())"
                                     py:content="buildDefinitionOptions(buildTemplateValueToIdMap, visibleBuildTypes, ordinal, bdef)" />
                                <tr id="pdbuilddef-empty" 
                                    py:attrs="{'style':productDefinition.getBuildDefinitions() and 'display: none;' or None}">
                                    <td colspan="5"><strong>No images defined.</strong></td>
                                </tr>
                            </tbody>
                            </table>
                            <table id="pdbuilddef-bt-all" style="display: none">
                                <tbody py:content="buildDefinitionOptions(buildTemplateValueToIdMap, visibleBuildTypes)" />
                            </table>
                            <p>
                            <a class="pdbuilddef-adder" href="#"><img src="${cfg.staticPath}/apps/mint/images/icon_add-n.gif" title="Add" />&nbsp;Add a new image</a></p>
                            <p>
                            <a id="learnmore" href="http://wiki.rpath.com/wiki/rBuilder:Image_Types" target="_blank">Read more about each image type</a></p>
                        </td>
                    </tr>
                    </table>
                    <p class="p-button">
                    <button class="img" type="button" onclick="ensureBuildsDefined()">
                        <div py:if="kwargs.has_key('linked')" py:strip="True">
                            <!--! When coming from the project page, the version already exists, so use the submit button -->
                            <img src="${cfg.staticPath}/apps/mint/images/submit_button.png" title="Update" />
                        </div>
                        <div py:if="not kwargs.has_key('linked')" py:strip="True">
                            <img py:if="isNew" src="${cfg.staticPath}/apps/mint/images/create_button.png" title="Create" />
                            <img py:if="not isNew" src="${cfg.staticPath}/apps/mint/images/submit_button.png" title="Submit" />
                        </div>
                    </button>
                    <a class="no-decoration" href="${project.getUrl()}" title="Cancel">
                        <img src="${cfg.staticPath}/apps/mint/images/cancel_button.png" />
                    </a>
                    </p>
                    <input type="hidden" name="id" value="${id}" />
                    <input py:if="kwargs.has_key('linked')" type="hidden" name="linked" value="${kwargs['linked']}" />
                    <input type="hidden" name="namespace" value="${kwargs['namespace']}" />
                    </form>
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
        </div>
        <div id="modalEditVersionWarning" title="Warning" style="display: none;">
            <p>
            No images have been added to this ${projectText().lower()} version's image set.
            </p>
            You will not be able to create an appliance until at least one image has 
            been added to the image set. You can do this now by clicking the 
            "Add a new image" link, or later by editing this ${projectText().lower()} version.
            <p>
            Would you like to add an image now, or add one later?
            </p>
        </div>
        </div>
    </body>
</html>
