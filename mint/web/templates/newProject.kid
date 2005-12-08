<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Create a Project</a>
    </div>

<?python
    for var in ['title', 'hostname', 'projecturl', 'optlists', 'blurb']:
        kwargs[var] = kwargs.get(var, '')
?>

    <head>
        <title>${formatTitle('Create a Project')}</title>
    </head>
    <body>
        <td id="main" class="spanleft" >
            <div class="pad">
                <p py:if="errors" class="error">Project Creation Error${len(errors) > 1 and 's' or ''}</p>
                <p py:for="error in errors" class="errormessage" py:content="error"/>
                <h2>Create a Project</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="createProject">

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Project Name:</em></th>
                            <td>
                                <input type="text" name="hostname" value="${kwargs['hostname']}" maxlength="16"/> .${cfg.projectDomainName}
                                <p class="help">Please choose a name for your project. This will be used as the hostname for your project site and repository (http://&lt;project-name&gt;.${cfg.projectDomainName}/) and the prefix for all of the project mailing lists. It must start with a letter and contain only letters and numbers, and be less than or equal to 16 characters long.</p>
                            </td>
                        </tr>

                        <tr>
                            <th><em class="required">Project Title:</em></th>
                            <td>
                                <input type="text" name="title" value="${kwargs['title']}"/>
                                <p class="help">The title is a longer, more descriptive name for your project. For example, <strong>My Custom Linux</strong></p>
                            </td>
                        </tr>

                        <tr>

                            <th>Project Description:</th>
                            <td>
                                <textarea rows="6" name="blurb" py:content="kwargs['blurb']"></textarea>
                                <p class="help">Please provide a description of your project and your goals for it.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>Project Home Page</th>
                            <td>
                                <input type="text" name="projecturl" value="${kwargs['projecturl']}"/>
                                <p class="help">Please enter the URL for an externally-hosted web page that will be linked from your project's main page.</p>
                            </td>
                        </tr>

                        <?python
                            from mint import mailinglists
                        ?>
                        <tr py:if="cfg.EnableMailLists">
                            <th>Mailing Lists:</th>
                            <td>
                                <p>By default, your project will be created with two mailing lists:</p>
                                    <ul>
                                        <li>&lt;project-name&gt;</li>
                                        <li>&lt;project-name&gt;-commits</li>
                                    </ul>

                                <p>You can also select the following lists to be created along with your project:</p>
                                <span py:for="listid in mailinglists.optionallists" style="margin-right: 1em;">
                                    <input class="check" type="checkbox"
                                           name="optlists" value="${listid}" py:attrs="{'checked': (kwargs['optlists'] and listid in kwargs['optlists']) and 'checked' or None}" />
                                        ${mailinglists.listnames[listid]%'projectname'}
                                </span>
                                <p class="help">Note that, once your project has been created, you can create new lists at any time from your
                                    project's administration page.</p>
                            </td>
                        </tr>
                        <tr py:if="self.auth.admin">
                            <td>
                            BLECK BLECK BLECK
                            </td>
                        </tr>
                    </table>
                    <p><button type="submit">Create</button></p>
                </form>
            </div>
        </td>
        <td id="right" class="plain">
            <div class="pad">
            </div>
        </td>
    </body>
</html>
