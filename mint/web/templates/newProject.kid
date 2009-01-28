<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.config import isRBO
    from mint.web.templatesupport import projectText
    for var in ['title', 'hostname', 'domainname', 'projecturl', 'optlists', 'blurb', 'shortname', 'namespace', 'version']:
        kwargs[var] = kwargs.get(var, '')
?>

    <head>
        <title>${formatTitle('Create a %s'%projectText().title())}</title>
    </head>
    <body>
    
        
    

        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            <div id="right" class="side">
                ${resourcePane()}
            </div>
            <div id="leftcenter">
            <div class="page-title-no-project">Create a ${projectText().title()}</div>
            <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form id="createForm" name="createForm" method="post" action="createProject">
            <table class="mainformhorizontal">
            <tr>
                <td class="form-label"><em class="required">${projectText().title()} Title:</em></td>
                <td>
                    <input type="text" autocomplete="off" name="title" value="${kwargs['title']}"/>
                    <p class="help">
                        Type a descriptive title for this ${projectText().lower()}.  Note that the version is
                        specified in a separate field, so the title should not contain the
                        version.  This descriptive title can be changed at any time as a way of
                        updating references to the ${projectText().lower()}.  For example: <strong>Example Appliance</strong>
                    </p>
                </td>
            </tr>
                    
            <tr>
                <td class="form-label"><em class="required">${projectText().title()} Type:</em></td>
                <td>
                     <input style="width: auto;" id="prodtype" type="radio" name="prodtype" value="Appliance" py:attrs="{'checked': (kwargs['prodtype'] == 'Appliance') and 'checked' or None}" checked="checked"/>
                     <label for="prodtype">Appliance</label>
                     <input style="width: auto;" id="prodtype" type="radio" name="prodtype" value="Component" py:attrs="{'checked': (kwargs['prodtype'] == 'Component') and 'checked' or None}" />
                     <label for="prodtype">Component</label>
                     <p class="help">Please select "Appliance" if this ${projectText().lower()}'s main purpose is to produce a software appliance.</p>
                </td>
            </tr>

            <tr>
                <td class="form-label"><em class="required">${projectText().title()} Short Name:</em></td>
                <td>
                    <input type="text" autocomplete="off" name="shortname" value="${kwargs['shortname']}" maxlength="16"/>
                    <p class="help">
                        Select a short name that reflects the ${projectText().lower()}'s identity.  This short
                        name is used to form the permanent repository hostname for the ${projectText().lower()}
                        as it resides in rBuilder.  Unlike the ${projectText().title()} Title, this value cannot 
                        be changed after it is set.  Carefully select a short name that starts
                        with a letter, contains only letters and numbers, and is up to 16 
                        characters long.  For example: <strong>exampleapp</strong>
                    </p>
                </td>
            </tr>

            <tr>
                <td class="form-label"><em class="required">${projectText().title()} Major Version:</em></td>
                <td>
                    <input type="text" name="version" value="${kwargs['version']}" size="16" maxlength="128"/>
                    <p class="help">
                        Type a ${projectText().title()} Major Version that reflects the new major version of the
                        appliance ${projectText().lower()}.  This does not have to correspond to the version 
                        of the software on the appliance.  Versions must start with an alphanumeric character
                        and can be followed by any number of other alphanumeric characters, separated if 
                        desired by decimals.  For example: '1', '1.0', '1.A', 'A1', and '2008' are all valid 
                        versions, but '2008 RC', '.', and '1.' are not valid.
                     </p>
                </td>
            </tr>
                    <tr py:if="availablePlatforms">
                        <td class="form-label">
                            <em class="required">Select Platform:</em>
                        </td>
                        <td>
                            <select name="platformLabel">
                                <option py:for="platformLabel, platformDesc in availablePlatforms" py:attrs="{'selected': (kwargs['platformLabel'] == platformLabel) and 'selected' or None}" value="${platformLabel}" py:content="platformDesc" />
                            </select>
                            <p class="help">Select a platform on which to base your appliance or component.</p>
                        </td>
                    </tr>
            </table>


            <h2>Advanced Options</h2>
            <table class="mainformhorizontal">
            <tr py:if="not isRBO()">
                <td class="form-label"><em class="required">Repository Domain Name:</em></td>
                <td>
                    <input type="text" name="domainname" value="${kwargs['domainname']}" />
                    <p class="help">
                        If an alternate domain name is required for this repository, it may
                        be typed here. The domain name will be appended to the Product Short
                        Name to form the permanent repository hostname, and can not be
                        changed after the ${projectText().lower()} is created. Typically,
                        the default is sufficient.
                    </p>
                </td>
            </tr>
            </table>
            <p class="p-button">
                <button class="img" type="submit">
                    <img src="${cfg.staticPath}/apps/mint/images/next_button.png" alt="Create" />
                </button>
            </p>
        </form>
        </div><br class="clear"/>
        <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
        <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
        <div class="bottom"/>
    </div>
    </body>
</html>
