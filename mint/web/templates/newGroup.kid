<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <?python
        for var in ['groupName', 'version', 'description']:
            kwargs[var] = kwargs.get(var, '')
    ?>

    <head>
        <title>${formatTitle('Create a Group')}</title>
    </head>
    <body>
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
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div class="page-title">
                    Create a Group</div>

                    <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                    <form method="post" action="createGroup">

                    <table class="mainformhorizontal">
                    <tr>
                        <td class="form-label">
                            <em class="required">Group Name:</em>
                        </td>
                        <td>group-</td>
                        <td>
                            <input type="text" name="groupName" value="${kwargs['groupName']}" size="16" maxlength="108"/>
                            <p class="help">Please choose a name for your group. "group-" is required and will be
                                automatically prepended to the name you enter.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label"><em class="required">Group Version:</em></td>
                        <td colspan="2">
                            <input type="text" name="version" size="16" maxlength="128" value="${kwargs['version']}"/>
                            <p class="help">Choose a version number for your group. Eg., 0.0.1</p>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label">Description:</td>
                        <td colspan="2">
                            <textarea rows="10" name="description">${kwargs['description']}</textarea>
                            <p class="help">Please enter a description of this group.</p>
                        </td>
                    </tr>
                    </table>
                    
                    <h2>Start Your Group</h2> 
                    <p class="help">You can choose some predefined groups of packages to add to your own group.
                        If you want to choose the individual troves entirely yourself, you don't have to select
                        any here.
                    </p>
                    <div py:strip="True" py:for="label in troves.keys()">
                        <p class="help">${messages[label]}</p>

                        <ul class="base-package-list">
                        <li py:for="t in troves[label]" py:if="t in metadata">
                            <input type="hidden" name="initialTrove" value="${t} ${troveDict[t][0].asString()} ${troveDict[t][1].freeze()}" py:if="t == 'group-appliance-platform'"/>
                            <input type="checkbox" class="check" py:if="t != 'group-appliance-platform'"
                                   name="initialTrove" py:attrs="{'checked': 'checked' and t == 'group-appliance-platform' or None,
                                                                  'disabled': 'disabled' and t == 'group-appliance-platform' or None}"
                                   value="${t} ${troveDict[t][0].asString()} ${troveDict[t][1].freeze()}" />
                            <input type="checkbox" class="check" py:if="t == 'group-appliance-platform'"
                                   name="dummyTrove" checked="checked" disabled="disabled" />
                            <b>${t}</b> - ${metadata.get(t, 'No Description')}
                        </li>
                        </ul>
                    </div>

                    <p class="p-button"><button id="newGroupSubmit" class="img" type="submit">
                        <img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" />
                    </button></p>
                    </form>
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
      