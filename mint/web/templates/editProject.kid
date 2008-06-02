<?xml version='1.0' encoding='UTF-8'?>
<?python 
    from mint import constants 
    from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('%s Settings: %s'%(projectText().title(),project.getNameForDisplay()))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

            <div id="spanleft">
                <h2>Edit ${projectText().title()} Properties</h2>
                <form method="post" action="${basePath}processEditProject">
                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th>
                                <em class="required">${projectText().title()} Title</em>
                            </th>
                            <td>
                                <input type="text" name="name" value="${kwargs['name']}" />
                                <p class="help">
                                    Type a descriptive title for this ${projectText().lower()}.  Note that the version is
                                    specified in a separate field, so the title should not contain the
                                    version.  This descriptive title can be changed at any time as a way of
                                    updating references to the ${projectText().lower()}.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th>${projectText().title()} Description</th>
                            <td>
                                <textarea name="desc" cols="70" rows="12">${kwargs['desc']}</textarea>
                            </td>
                        </tr>
                        <tr>
                            <th>${projectText().title()} Home Page</th>
                            <td>
                                <input type="text" name="projecturl" value="${kwargs['projecturl']}" />
                                <p class="help">
                                    Type a URL for an externally-hosted web page that can be identified as
                                    the ${projectText().lower()}'s main online resource.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th>Repository Commits Email</th>
                            <td>
                                <input type="text" name="commitEmail" value="${kwargs['commitEmail']}" />
                                <p class="help">
                                    Type an email address to which notices are sent when users save
                                    work to the ${projectText().lower()}'s repository.  Emails include the commit messages 
                                    required when "committing" ("checking in" or "saving") anything to a 
                                    Conary repository during appliance development.  Emails also include 
                                    Conary's summary of what was committed, typically a list of things that 
                                    changed between the previous commit and the current commit.
                                </p>
                            </td>
                        </tr>

                    </table>

                    <button class="img" type="submit"><img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" /></button>
                </form>
            </div>
        </div>
    </body>
</html>
