<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Create a Project</a>
    </div>

    <?python
        for var in ['groupName', 'version', 'description']:
            kwargs[var] = kwargs.get(var, '')
    ?>

    <head>
        <title>${formatTitle('Create a Group Trove')}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main" class="main" >
            <div class="pad">
                <p py:if="errors" class="error">Group Trove Creation Error${len(errors) > 1 and 's' or ''}</p>
                <p py:for="error in errors" class="errormessage" py:content="error"/>
                <h2>Create a Group Trove</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="editGroup">

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
                                <p class="help">Choose a version number for your group. Eg., 0.5.0</p>
                            </td>
                        </tr>
                        <tr>
                            <th colspan="2">Description:</th>
                            <td>
                                <textarea rows="10" cols="70" name="description">${kwargs['description']}</textarea>
                                <p class="help">Please enter a description of this group.</p>
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
