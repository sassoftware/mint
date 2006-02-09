<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="administer?operation=external">Add External Project</a>
    </div>

    <head>
        <title>${formatTitle('Add External Project')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
              <form action="administer" method="post">
                <h2>Add External Project</h2>
                <p py:if="firstTime" class="help">External projects have the same structure as local projects, except that the repository is not contained locally. Hence ${cfg.productName} will need to ask you for the same sorts of information that you'd need to provide when creating a new local project. Since nearly everyone will want rPath Linux as an external project, ${cfg.productName} has pre-populated those values.</p>
                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                  <tr>
                    <th><em class="required">Project Name:</em></th>
                    <td>
                      <input type="text" name="hostname" maxlength="16" value="${firstTime and 'rpath' or ''}"/>
                      <p class="help">You can choose a local name for this project. This will be used as the hostname for this project's site and repository (http://&lt;project-name&gt;.${cfg.projectDomainName}/). It must start with a letter and contain only letters and numbers, and be less than or equal to 16 characters long.</p>
                      <p class="help">To reduce confusion, it is recommended that you copy the name of the external project.</p>
                    </td>
                  </tr>
                  <tr>
                      <th><em class="required">Project Title:</em></th>
                      <td>
                        <input type="text" name="name" value="${firstTime and 'rPath Linux' or ''}"/>
                        <p class="help">The title is a longer, more descriptive name for this project. For example, <strong>My Custom Linux</strong></p>
                        <p class="help">To reduce confusion, it is recommended that you copy the title of the external project.</p>
                      </td>
                  </tr>
                  <tr>
                    <th><em class="required">Project Label:</em></th>
                    <td>
                      <input type="text" name="label" value="${firstTime and 'conary.rpath.com@rpl:1' or ''}"/>
                      <p class="help">Please enter the label of the external project. This is basically an installLabelPath.</p>
                    </td>
                  </tr>
                  <tr>
                    <th>URL:</th>
                    <td>
                      <input type="text" name="url" value="${firstTime and 'http://conary.rpath.com/conary/' or ''}"/>
                      <p class="help">If a URL is not provided it will automatically be computed from the project's label. eg; <strong>conary.rpath.com@rpl:1</strong> will translate to <strong>http://conary.rpath.com/conary/</strong></p>
                    </td>
                  </tr>
                  </table>
                  <button name="operation" value="process_external" class="img" type="submit"><img src="${cfg.staticPath}/apps/mint/images/create_button.png" alt="Create" /></button>
              </form>
            </div>
        </td>
    </body>
</html>
