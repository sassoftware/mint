<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Add External Project')}</title>
    </head>
    <body>
        <a href ="${cfg.basePath}admin/">Return to Administrator Page</a>
        <td id="main" class="spanall">
            <div class="pad">
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
                      <input type="text" name="hostname" maxlength="16" value="${firstTime and 'rpath' or ''}"/>
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
                        <input type="text" name="name" value="${firstTime and 'rPath Linux' or ''}"/>
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
                      <input type="text" name="label" value="${firstTime and 'conary.rpath.com@rpl:1' or ''}"/>
                      <p class="help">Enter this project's label.  For
                      example, <strong>conary.example.com@rpl:1</strong></p>
                    </td>
                  </tr>
                  <tr>
                    <th>Repository URL:</th>
                    <td>
                      <input type="text" name="url" value="${firstTime and 'http://conary.rpath.com/conary/' or ''}"/>
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

                <h2>Mirror Settings</h2>
                <table class="mainformhorizontal">
                  <tr>
                    <th>Mirroring Enabled:</th>
                    <td><input type="checkbox" class="check" name="useMirror" value="1" /> Mirror this repository locally.</td>
                  </tr>
                  <tr>
                    <th>Authorization:</th>
                    <td>Username: <input type="text" name="mirrorUser" style="width: 25%;" /></td>
                  </tr>
                  <tr>
                    <th></th>
                    <td>Password: <input type="password" name="mirrorPass" style="width: 25%;" />
                      <p class="help">
                          Enter the username and password of a user authorized to mirror this repository.
                      </p>
                      <p class="help">
                          If you have a mirroring entitlement instead of a username and
                          password, please paste it here:
                      </p>
                      <textarea rows="5" cols="50" name="mirrorEnt" />
                    </td>
                  </tr>
                  </table>
                  <button class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add" /></button>
              </form>
            </div>
        </td>
    </body>
</html>
