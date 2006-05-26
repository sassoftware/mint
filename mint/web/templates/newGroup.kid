<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
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

            <div id="spanright">
                <h2>Create a Group</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="createGroup">

                    <table>
                        <tr>
                            <th>
                                <em class="required">Group Name:</em>
                            </th>
                            <td>group-</td>
                            <td>
                                <input type="text" name="groupName" value="${kwargs['groupName']}" size="16" maxlength="108"/>
                                <p class="help">Please choose a name for your group. "group-" is required and will be
                                    automatically prepended to the name you enter.
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th><em class="required">Group Version:</em></th>
                            <td colspan="2">
                                <input type="text" name="version" size="16" maxlength="128" value="${kwargs['version']}"/>
                                <p class="help">Choose a version number for your group. Eg., 0.0.1</p>
                            </td>
                        </tr>
                        <tr>
                            <th>Description:</th>
                            <td colspan="2">
                                <textarea rows="10" cols="70" name="description">${kwargs['description']}</textarea>
                                <p class="help">Please enter a description of this group.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>Start Your Group:</th>
                            <td colspan="2">
                                <p class="help">You can choose some predefined groups of packages to add to your own group.
                                    If you want to choose the individual troves entirely yourself, you don't have to select
                                    any here.
                                </p>
                                <p class="help">These troves come from rPath Linux on the conary.rpath.com@rpl:1 label</p>

                                <ul>
                                    <li py:for="t in troves" py:if="metadata[t]">
                                        <input type="hidden" name="initialTrove" value="${t} ${troveDict[t][0].asString()} ${troveDict[t][1].freeze()}" py:if="t == 'group-core'"/>
                                        <input type="checkbox" class="check" py:if="t != 'group-core'"
                                               name="initialTrove" py:attrs="{'checked': 'checked' and t == 'group-core' or None,
                                                                              'disabled': 'disabled' and t == 'group-core' or None}"
                                               value="${t} ${troveDict[t][0].asString()} ${troveDict[t][1].freeze()}" />
                                            <b>${t}</b> - ${metadata[t]}
                                    </li>
                                </ul>
                            </td>
                        </tr>
                    </table>
                    <p><button class="img" type="submit">
                        <img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" />
                    </button></p>
                </form>
            </div>
        </div>
    </body>
</html>
