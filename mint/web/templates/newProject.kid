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
                <td class="form-label">
                    ${formLabelWithHelp("title_help", projectText().title() + " Title")}
                </td>
                <td>
                    <input type="text" autocomplete="off" name="title" value="${kwargs['title']}"/>
                    <div id="title_help" class="help" style="display: none;">
                        Type a descriptive title for this ${projectText().lower()}.  Note that the version is
                        specified in a separate field, so the title should not contain the
                        version.  This descriptive title can be changed at any time as a way of
                        updating references to the ${projectText().lower()}.  For example: <strong>Example Appliance</strong>
                    </div>
                </td>
            </tr>

            <tr>
                <td class="form-label">
                    ${formLabelWithHelp("sn_help", projectText().title() + " Short Name")}
                </td>
                <td>
                    <input type="text" autocomplete="off" name="shortname" value="${kwargs['shortname']}" maxlength="16"/>
                    <div id="sn_help" class="help" style="display: none;">
                        Select a short name that reflects the ${projectText().lower()}'s identity.  This short
                        name is used to form the permanent repository hostname for the ${projectText().lower()}
                        as it resides in rBuilder.  Unlike the ${projectText().title()} Title, this value cannot 
                        be changed after it is set.  Carefully select a short name that starts
                        with a letter, contains only letters and numbers, and is up to 16 
                        characters long.  For example: <strong>exampleapp</strong>
                    </div>
                </td>
            </tr>

            <tr>
                <td class="form-label">
                    ${formLabelWithHelp("version_help", projectText().title() + " Major Version")}
                </td>
                <td>
                    <input type="text" name="version" value="${kwargs['version']}" size="16" maxlength="128"/>
                    <div id="version_help" class="help" style="display: none;">
                        Type a ${projectText().title()} Major Version that reflects the new major version of the
                        appliance ${projectText().lower()}.  This does not have to correspond to the version 
                        of the software on the appliance.  Versions must start with an alphanumeric character
                        and can be followed by any number of other alphanumeric characters, separated if 
                        desired by decimals.  For example: '1', '1.0', '1.A', 'A1', and '2008' are all valid 
                        versions, but '2008 RC', '.', and '1.' are not valid.
                     </div>
                </td>
            </tr>
            
            <tr py:if="availablePlatforms">
                <td class="form-label">
                    ${formLabelWithHelp("platform_help", projectText().title() + " Platform")}
                </td>
                <td>
                    <select name="platformLabel">
                        <option py:for="platformLabel, platformDesc in availablePlatforms" py:attrs="{'selected': (kwargs['platformLabel'] == platformLabel) and 'selected' or None}" value="${platformLabel}" py:content="platformDesc" />
                    </select>
                    <div id="platform_help" class="help" style="display: none;">
                        Select a platform on which to base your appliance or component.
                    </div>
                </td>
            </tr>
            </table>

            <div class="expandableFormGroupTitle" onclick="javascript:toggle_display('advanced_settings');">
                <img id="advanced_settings_expander" class="noborder" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" />
                Advanced Options
            </div>
            <div id="advanced_settings" class="formgroup" style="display: none;">
                <table class="mainformhorizontal">
                <tr py:if="not isRBO()">
                    <td class="form-label">
                        ${formLabelWithHelp("dn_help", "Repository Domain Name")}
                    </td>
                    <td>
                        <input type="text" name="domainname" value="${kwargs['domainname']}" />
                        <div id="dn_help" class="help" style="display: none;">
                            If an alternate domain name is required for this repository, it may
                            be typed here. The domain name will be appended to the Product Short
                            Name to form the permanent repository hostname, and can not be
                            changed after the ${projectText().lower()} is created. Typically,
                            the default is sufficient.
                        </div>
                    </td>
                </tr>            
                </table>
            </div>
            <p class="p-button">
                <button class="img" type="submit">
                    <img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" />
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
