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
        <![CDATA[ 
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
                if(isPrivate) {
                   if(!isPrivate.checked) {
                      modalYesNo(handleYes, handleNo);
                   }
                }
            }
        ]]>
        </script>
    
       <div id="layout">

            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            <div id="innerpage">
                <img id="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img id="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>

                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">Edit ${projectText().title()} Properties</div>
                    
                    <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                    <form method="post" action="${basePath}processEditProject">
                    <table class="mainformhorizontal">
                    <tr>
                        <td class="form-label"><em class="required">${projectText().title()} Title:</em></td>
                        <td>
                            <input type="text" name="name" value="${kwargs['name']}" />
                            <p class="help">
                                Type a descriptive title for this ${projectText().lower()}.  Note that the version is
                                specified in a separate field, so the title should not contain the
                                version.  This descriptive title can be changed at any time as a way of
                                updating references to the ${projectText().lower()}.</p>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label">Description:</td>
                        <td>
                            <textarea name="desc" cols="70" rows="12">${kwargs['desc']}</textarea>
                        </td>
                    </tr>
                    <tr>
                        <td class="form-label">Home Page:</td>
                        <td>
                            <input type="text" name="projecturl" value="${kwargs['projecturl']}" />
                            <p class="help">
                                Type a URL for an externally-hosted web page that can be identified as
                                the ${projectText().lower()}'s main online resource.</p>
                        </td>
                    </tr>
                    </table>
                    
                    <h2>Advanced Options</h2>
                    <table class="mainformhorizontal">
                    <tr>
                        <td class="form-label">Is Private:</td>
                        <td>
                        <div py:if="kwargs['isPrivate']" py:strip="True">
                            <input type="checkbox" class='check' name="isPrivate" id="isPrivate" onclick="return handleVisibility()" py:attrs="{'checked' : kwargs['isPrivate'] and 'checked' or None}"/>
                            <div id="modalYesNo" title="Confirmation" style="display: none;">
                                If this ${projectText().title()} is public, it will open ${projectText().title()} repositories
                                and releases to the general public. You will not be able to revert back to a private 
                                ${projectText().title()}. Are you sure you want to make this ${projectText().title()} public?
                            </div>
                            <p class="help">
                                Check this box if you want your Private ${projectText().title()} to be made Public. Public
                                ${projectText().title()}s are visible to all users whether they are a ${projectText().title()} 
                                Team Member or not. Once your ${projectText().title()} is public you cannot make it private again.</p>
                        </div>
                        <div py:if="not kwargs['isPrivate']" py:strip="True">
                            <div py:if="not auth.admin" py:strip="True">
                                This ${projectText().title()} is public and cannot be made private.
                                <input type="hidden" name="isPrivate" id="isPrivate" value="kwargs['isPrivate']"/>
                            </div>
                            <div py:if="auth.admin" py:strip="True">
                                <input type="checkbox" class='check' name="isPrivate" id="isPrivate" onclick="return handleVisibility()" py:attrs="{'checked' : kwargs['isPrivate'] and 'checked' or None}"/>
                                <p class="help">
                                    Check the box if you want this ${projectText().title()} to be private. 
                                    Private ${projectText().title()}s are only accessible by ${projectText().title()} 
                                    team members (owners, developers, and users). </p>
                            </div>
                        </div></td>
                    </tr>
                    
                    <tr>
                        <td class="form-label">Commit Email:</td>
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
                        
                        <tr>
                            <th><em class="required">${projectText().title()} Namespace:</em></th>
                            <td>
                                <input type="text" name="namespace" value="${kwargs['namespace']}" size="16" maxlength="128"/>
                                <p class="help">
                                    Type a ${projectText().title()} Namespace for your appliance ${projectText().lower()}.  
                                    Namespaces usually represent the organization behind the ${projectText().lower()}, or the namespace of
                                    the ${projectText().lower()} that is being derived.  Namespaces must start with an alphanumeric
                                    character and can be followed by any number of other alphanumeric characters.
                                    For example: <strong>rpath</strong>, <strong>rpl</strong>, and <strong>fl</strong> 
                                    are all valid namespaces, but 'rPath Linux', and '#' are not valid.
                                 </p>
                            </td>
                        </tr>
                    </table>

                   <p class="p-button"><button class="img" type="submit"><img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" /></button></p>
                    </form>
                </div><br class="clear" />
                <img id="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img id="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
