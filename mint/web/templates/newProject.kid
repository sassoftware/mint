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
    for var in ['title', 'hostname', 'domainname', 'projecturl', 'optlists', 'blurb', 'shortname', 'version', 'commitEmail']:
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
                        <th><em class="required">${projectText().title()} Title:</em></th>
                        <td>
                            <input type="text" autocomplete="off" name="title" value="${kwargs['title']}"/>
                            <p class="help">The title should be a descriptive name for your ${projectText().lower()}. For example, <strong>My Custom Linux</strong></p>
                        </td>
                    </tr>

                    <tr>
                        <th><em class="required">${projectText().title()} Short Name:</em></th>
                        <td>
                            <input type="text" autocomplete="off" name="shortname" value="${kwargs['shortname']}" maxlength="16"/>
                            <p class="help">The short name should reflect your ${projectText().lower()}'s identity (for example <tt>custlinux</tt>).  It must start with a letter, contain only letters and numbers, and be less than or equal to 16 characters long. <a class="learnmore" href="http://${SITE}help?page=lm-project-naming" onclick="javascript:window.open(this.href,'rbohelp','width=400,height=400,scrollbars,resizable');return false;">Learn more</a></p>
                        </td>
                    </tr>

                    <tr>
                        <th><em class="required">${projectText().title()} Version:</em></th>
                        <td>
                            <input type="text" name="version" value="${kwargs['version']}" size="16" maxlength="128"/>
                            <p class="help">
                                Choose an initial version for your product. Versions may contain
                                any combination of alphanumeric characters and decimals but
                                cannot contain any spaces (for example, '1', 'A', '1.0', '2007' are
                                all legal versions, but '1.0 XL' is not).
                             </p>
                        </td>
                    </tr>

                    <tr>
                        <th><em class="required">${projectText().title()} Type:</em></th>
                        <td>
                            <input style="width: auto;" id="prodtype" type="radio" name="prodtype" value="Appliance" py:attrs="{'checked': (kwargs['prodtype'] == 'Appliance') and 'checked' or None}" checked="checked"/>
                            <label for="prodtype">Appliance</label>
                            <input style="width: auto;" id="prodtype" type="radio" name="prodtype" value="Component" py:attrs="{'checked': (kwargs['prodtype'] == 'Component') and 'checked' or None}" />
                            <label for="prodtype">Component</label>
                            <p class="help">Please select "Appliance" if this ${projectText().lower()}'s main purpose is to produce a software appliance.</p>
                        </td>
                    </tr>

                    <tr>
                        <th>${projectText().title()} Description:</th>
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
                <p><button class="img" type="submit">
                    <img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" />
                </button></p>
                <input type="hidden" name="domainname" value="${kwargs['domainname']}" />
            </form>
        </div>
    </body>
</html>
