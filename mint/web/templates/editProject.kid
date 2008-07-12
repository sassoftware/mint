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
    
        <script type="text/javascript">
        <!-- 
            function handleYes() {
                var isPrivate = document.getElementById('isPrivate');
                if(isPrivate) {
                   isPrivate.checked = false;
                }
            }
            
            function handleNo() {
                var isPrivate = document.getElementById('isPrivate');
                if(isPrivate) {
                   isPrivate.checked = true;
                }
            }
        
            function handleVisibility() {
                var isPrivate = document.getElementById('isPrivate');
                if(isPrivate && !isPrivate.checked) {
                   modalYesNo(handleYes, handleNo);
                }
            }
        //-->
        </script>
    
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
                    </table>
                    
                    <h3>Advanced Options</h3>
                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
    
                        <tr>
                            <th>${projectText().title()} is Private:</th>
                            <td>
                                <div py:if="kwargs['isPrivate']" py:strip="True">
                                    <input type="checkbox" class='check' name="isPrivate" id="isPrivate" onclick="return handleVisibility()" py:attrs="{'checked' : kwargs['isPrivate'] and 'checked' or None, 'disabled' : not kwargs['isPrivate'] and 'checked' or None}"/>
                                    <div id="modalYesNo" title="Confirmation" style="display: none;">
                                        Making this ${projectText().title()} public will open 
                                        ${projectText().title()} repositories and Releases to 
                                        the general public. You will not be able to revert back 
                                        to a private ${projectText().title()}. Are you sure you 
                                        want to make this ${projectText().title()} public?
                                    </div>
                                    <p class="help">
                                        Check the box if you want your Private ${projectText().title()} 
                                        to become public. Public ${projectText().title()}s are visible 
                                        to all users whether they are a ${projectText().title()} Team 
                                        Member or not. Once your ${projectText().title()} is public you
                                        cannot make it private again.
                                    </p>
                                </div>
                                <div py:if="not kwargs['isPrivate']" py:strip="True">
                                    This ${projectText().title()} is public and cannot be made private.
                                    <input type="hidden" name="isPrivate" id="isPrivate" value="kwargs['isPrivate']"/>
                                </div>
                            </td>
                        </tr>
                        
                        <tr>
                            <th>Repository Commits Email:</th>
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
