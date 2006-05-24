<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->

<?python
    for var in ['name', 'hostname', 'label', 'url', 'externalUser', 'externalPass', 'externalEntKey', 'externalEntClass', 'authType', 'useMirror', 'primeMirror', 'externalAuth', 'authType']:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title>${formatTitle('Add External Project')}</title>
    </head>
    <body onload="javascript:hideElement('mirrorSettings'); hideElement('authSettings')">
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
          <form action="${cfg.basePath}admin/processExternal" method="post">
            <h2>Add External Project</h2>
            <p class="help">External projects appear just like the
            projects you host on ${cfg.productName} with one exception:
            the respository is <em>not</em> stored on
            ${cfg.productName}.  External projects are useful for
            integrating the contents of another organization's
            repository into ${cfg.productName}, making it easier for
            your users to reference that organization's work in
            theirs.</p>

            <p py:if="firstTime" class="help">Because you have not yet
            added rPath Linux as an external project, the following
            fields have been pre-populated to make adding rPath Linux
            easy.  If you do not wish to add rPath Linux as an external
            project, you can erase the contents of each field and add
            the appropriate information for the external project you
            wish to add.</p>

            <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
              <tr>
                <th><em class="required">Project Name:</em></th>
                <td>
                  <input type="text" autocomplete="off" name="hostname" maxlength="16" value="${kwargs['hostname']}"/>
                  <p class="help">Enter a local name for this
                  project. The local name will be used as the hostname
                  for this project's site and repository
                  (http://&lt;project-name&gt;.${cfg.projectDomainName}/). It
                  must start with a letter and contain only letters and
                  numbers, and be less than or equal to 16 characters
                  long.  For example, <strong>mylinux</strong></p>

                  <p class="help">(To reduce confusion, we recommend
                  that you enter the external project's name.)</p>
                </td>
              </tr>
              <tr>
                  <th><em class="required">Project Title:</em></th>
                  <td>
                    <input type="text" autocomplete="off" name="name" value="${kwargs['name']}"/>
                    <p class="help">Enter a local title for this
                    project.  The title is a longer, more descriptive
                    name for the project. For example, <strong>My
                    Custom Linux</strong></p>

                   <p class="help">(To reduce confusion, we recommend
                   that you enter the external project's title.)</p>
                  </td>
              </tr>
              <tr>
                <th><em class="required">Project Label:</em></th>
                <td>
                  <input type="text" autocomplete="off" name="label" value="${kwargs['label']}" />
                  <p class="help">Enter this project's label.  For
                  example, <strong>conary.example.com@rpl:1</strong></p>
                </td>
              </tr>
              <tr>
                <th>Repository URL:</th>
                <td>
                  <input type="text" autocomplete="off" name="url" value="${kwargs['url']}"/>
                  <p class="help">Enter the URL for this project's
                  repository.  If a URL is not provided, the standard
                  URL format will be derived from the project's label
                  (eg; for label
                  <strong>conary.example.com@rpl:1</strong> the
                  repository URL will be
                  <strong>http://conary.example.com/conary/</strong>)</p>
                </td>
              </tr>
            </table>


            <h2>Authentication</h2>
            <p><b>
                <input onclick="javascript:toggle_element_by_checkbox('authSettings', 'externalAuth');"
                    type="checkbox" class="check" name="externalAuth" value="1" id="externalAuth" py:attrs="{'checked': kwargs['externalAuth'] and 'checked' or None}" />
                <label for="externalAuth">External repository requires authentication</label>
            </b></p>
            <table class="mainformhorizontal" id="authSettings">
                <tr>
                    <td><input id="authTypeUserPass" type="radio" class="check" name="authType" value="userpass" py:attrs="{'checked': (kwargs['authType'] == 'userpass') and 'checked' or None}"/><label for="authTypeUserPass">Use username/password</label>
                    </td>
                </tr>
                <tr>
                    <th style="padding-left: 3em;">Username:</th>
                    <td><input type="text" autocomplete="off" name="externalUser" style="width: 25%;" value="${kwargs['externalUser']}" /></td>
                </tr>
                <tr>
                    <th style="padding-left: 3em;">Password:</th>
                    <td><input type="password" autocomplete="off" name="externalPass" style="width: 25%;" value="${kwargs['externalPass']}" /></td>
                </tr>
                <tr>
                    <td><input id="authTypeEnt" type="radio" class="check" name="authType" value="entitlement" py:attrs="{'checked': (kwargs['authType'] == 'entitlement') and 'checked' or None}" /><label for="authTypeEnt">Use an entitlement</label>
                    </td>
                </tr>
                <tr>
                    <th style="padding-left: 3em;">Entitlement Class:</th>
                    <td>
                        <input type="text" autocompelete="off" name="externalEntClass" value="${kwargs['externalEntClass']}" />
                    </td>
                </tr>
                <tr>
                    <th style="padding-left: 3em;">Entitlement Key:</th>
                    <td>
                        <textarea rows="5" cols="50" name="externalEntKey"  py:content="kwargs['externalEntKey']" />
                    </td>
                </tr>
            </table>


            <h2>Mirror Settings</h2>
            <p><b>
                <input onclick="javascript:toggle_element_by_checkbox('mirrorSettings', 'useMirror');"
                    type="checkbox" class="check" name="useMirror" value="1" id="useMirror" py:attrs="{'checked': kwargs['useMirror'] and 'checked' or None}" />
                <label for="useMirror">Mirror this repository locally</label>
            </b></p>
            <table class="mainformhorizontal" id="mirrorSettings">
                <tr>
                    <th>Preload this mirror:</th>
                    <td>
                        <input type="checkbox" class="check" name="primeMirror" id="primeMirror" value="1" py:attrs="{'checked': kwargs['primeMirror'] and 'checked' or None}" />
                        <label for="primeMirror">Preload this mirror with a set of CDs or DVDs</label>
                    </td>
                </tr>
            </table>
            <button class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add" /></button>
        </form>
        </div>
    </body>
</html>
