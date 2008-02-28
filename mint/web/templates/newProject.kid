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
    for var in ['title', 'hostname', 'domainname', 'projecturl', 'optlists', 'blurb', 'commitEmail']:
        kwargs[var] = kwargs.get(var, '')
?>

    <head>
        <title>${formatTitle('Create a %s'%projectText().title())}</title>
    </head>
    <body>
        <div id="layout">
            <h2>Create a ${projectText().title()}</h2>
            <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form method="post" action="createProject" >

                <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                    <tr>
                        <th><em class="required">${projectText().title()} Name:</em></th>
                        <td>
                            <input type="text" autocomplete="off" name="hostname" value="${kwargs['hostname']}" maxlength="16"/>&nbsp;.${kwargs['domainname']}

                            <p class="help">Please choose a name for your ${projectText().lower()}. This will be used as the hostname for your ${projectText().lower()} site and repository (http://&lt;${projectText().lower()}-name&gt;.${kwargs['domainname']}/). It must start with a letter and contain only letters and numbers, and be less than or equal to 16 characters long.</p>
                        </td>
                    </tr>

                    <tr>
                        <th><em class="required">${projectText().title()} Title:</em></th>
                        <td>
                            <input type="text" autocomplete="off" name="title" value="${kwargs['title']}"/>
                            <p class="help">The title is a longer, more descriptive name for your ${projectText().lower()}. For example, <strong>My Custom Linux</strong></p>
                        </td>
                    </tr>
                    <tr>
                        <th>Is This a Software Appliance?</th>
                        <td>
                            <select style="width: auto;" name="appliance">
                                <option py:attrs="{'selected': 'selected' and (kwargs['appliance'] in ('unknown', '')) or None}" value="unknown">---</option>
                                <option py:attrs="{'selected': 'selected' and (kwargs['appliance'] == 'yes') or None}" value="yes">Yes</option>
                                <option py:attrs="{'selected': 'selected' and (kwargs['appliance'] == 'no') or None}" value="no">No</option>
                            </select>
                            <p class="help">Please select "yes" if this ${projectText().lower()}'s main purpose is to produce a software appliance.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>${projectText().title()} Description</th>
                        <td>
                            <textarea rows="6" cols="72" name="blurb" py:content="kwargs['blurb']"></textarea>
                            <p class="help">Please provide a description of your ${projectText().lower()} and your goals for it.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>${projectText().title()} Home Page</th>
                        <td>
                            <input type="text" name="projecturl" value="${kwargs['projecturl']}"/>
                            <p class="help">Please enter the URL for an externally-hosted web page that will be linked from your ${projectText().lower()}'s main page.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>Repository Commits Email</th>
                        <td>
                            <input type="text" name="commitEmail" value="${kwargs['commitEmail']}" />
                            <p class="help">An email address to which Conary repository commit messages are sent.</p>
                        </td>
                    </tr>
                </table>
                <p><button class="img" type="submit" id="newProject">
                    <img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" />
                </button></p>
                <input type="hidden" name="domainname" value="${kwargs['domainname']}" />
            </form>
        </div>
    </body>
</html>
