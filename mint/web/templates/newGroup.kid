<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Create a Group</a>
    </div>

    <?python
        for var in ['groupName', 'version', 'description']:
            kwargs[var] = kwargs.get(var, '')
    ?>

    <head>
        <title>${formatTitle('Create a Group')}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main" class="main" >
            <div class="pad" >
                <p py:if="errors" class="error">Group Creation Error${len(errors) > 1 and 's' or ''}</p>
                <p py:for="error in errors" class="errormessage" py:content="error"/>
                <h2>Create a Group</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="createGroup">

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th>
                                <em class="required">Group Name:</em>
                            </th>
                            <td>group-</td>
                            <td>
                                <input type="text" name="groupName" value="${kwargs['groupName']}" size="16" maxlength="16"/>
                                <p class="help">Please choose a name for your group. "group-" is required and will be
                                    automatically prepended to the name you enter.
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th colspan="2"><em class="required">Group Version:</em></th>
                            <td>
                                <input type="text" name="version" size="16" value="${kwargs['version']}"/>
                                <p class="help">Choose a version number for your group. Eg., 0.0.1</p>
                            </td>
                        </tr>
                        <tr>
                            <th colspan="2">Description:</th>
                            <td>
                                <textarea rows="10" cols="70" name="description">${kwargs['description']}</textarea>
                                <p class="help">Please enter a description of this group.</p>
                            </td>
                        </tr>
                        <tr>
                            <th colspan="2">Start Your Group:</th>
                            <td>
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
                    <p><button type="submit">Create</button></p>
                </form>
            </div>
        </td>
        <td id="right" class="projects">
            ${projectsPane()}
        </td>
    </body>
</html>
