<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->

<?python
    from mint.web.templatesupport import projectText
    for var in ['name', 'hostname', 'label', 'url',
        'externalUser', 'externalPass', 'externalEntKey',
        'authType', 'useMirror',
        'externalAuth', 'authType', 'additionalLabelsToMirror',
        'allLabels']:
        kwargs[var] = kwargs.get(var, initialKwargs.get(var, ''))
?>
    <head>
        <title>${formatTitle((editing and 'Edit' or 'Add') + ' External %s'%projectText().title())}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
          <form action="${cfg.basePath}admin/processAddExternal" method="post">
            <h2>${editing and 'Edit ' or 'Add '} External ${projectText().title()}</h2>
            <p py:if="not editing" class="help">External ${projectText().lower()}s appear just like the
            ${projectText().lower()}s you host on ${cfg.productName} with one exception:
            the respository is <em>not</em> stored on
            ${cfg.productName}.  External ${projectText().lower()}s are useful for
            integrating the contents of another organization's
            repository into ${cfg.productName}, making it easier for
            your users to reference that organization's work in
            theirs.</p>

            <p py:if="firstTime" class="help">Because you have not yet
            added rPath Linux as an external ${projectText().lower()}, the following
            fields have been pre-populated to make adding rPath Linux
            easy.  If you do not wish to add rPath Linux as an external
            ${projectText().lower()}, you can erase the contents of each field and add
            the appropriate information for the external ${projectText().lower()} you
            wish to add.</p>

            <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
              <tr>
                <th><em class="required">${projectText().title()} Name:</em></th>
                <td>
                    <input type="${editing and 'hidden' or 'text'}" autocomplete="off" name="hostname" maxlength="16" value="${kwargs['hostname']}"/>
                    <div py:if="editing">${kwargs['hostname']}</div>
                    <p py:if="not editing" class="help">Enter a local name for this
                    ${projectText().lower()}. The local name will be used as the hostname
                    for this ${projectText().lower()}'s site and repository
                    (http://&lt;${projectText().lower()}-name&gt;.${cfg.projectDomainName}/). It
                    must start with a letter and contain only letters and
                    numbers, and be less than or equal to 16 characters
                    long.  For example, <strong>mylinux</strong></p>

                    <p py:if="not editing" class="help">(To reduce confusion, we recommend
                    that you enter the external ${projectText().lower()}'s name.)</p>
                </td>
              </tr>
              <tr>
                  <th><em class="required">${projectText().title()} Title:</em></th>
                  <td>
                    <input type="text" autocomplete="off" name="name" value="${kwargs['name']}"/>
                    <p class="help">Enter a local title for this
                    ${projectText().lower()}.  The title is a longer, more descriptive
                    name for the ${projectText().lower()}. For example, <strong>My
                    Custom Linux</strong></p>

                   <p class="help">(To reduce confusion, we recommend
                   that you enter the external ${projectText().lower()}'s title.)</p>
                  </td>
              </tr>
              <tr>
                <th><em class="required">${projectText().title()} Label:</em></th>
                <td>
                  <input type="text" autocomplete="off" name="label" value="${kwargs['label']}" />
                  <p class="help">Enter this ${projectText().lower()}'s label.  For
                  example, <strong>conary.example.com@rpl:1</strong></p>
                </td>
              </tr>
              <tr>
                <th>Repository URL:</th>
                <td>
                  <input type="text" autocomplete="off" name="url" value="${kwargs['url']}"/>
                  <p class="help">Enter the URL for this ${projectText().lower()}'s
                  repository.  If a URL is not provided, the standard
                  URL format will be derived from the ${projectText().lower()}'s label
                  (eg; for label
                  <strong>conary.example.com@rpl:1</strong> the
                  repository URL will be
                  <strong>http://conary.example.com/conary/</strong>)</p>
                </td>
              </tr>
            </table>


            <h2>Authentication</h2>
            <table class="mainformhorizontal" id="authSettings">
                <tr>
                    <td colspan="2"><input id="authTypeNone" type="radio" class="check" name="authType" value="none"
                        py:attrs="{'checked': (kwargs['authType'] == 'none') and 'checked' or None}"/>
                        <label for="authTypeNone">Anonymous access only</label>
                    </td>
                </tr>
                <tr>
                    <td colspan="2"><input id="authTypeUserPass" type="radio" class="check" name="authType" value="userpass" py:attrs="{'checked': (kwargs['authType'] == 'userpass') and 'checked' or None}"/><label for="authTypeUserPass">Use username/password</label>
                    </td>
                </tr>
                <tr>
                    <th style="padding-left: 3em; width: 25%;">Username:</th>
                    <td><input type="text" autocomplete="off" name="externalUser" style="width: 25%;" value="${kwargs['externalUser']}" /></td>
                </tr>
                <tr>
                    <th style="padding-left: 3em; width: 25%;">Password:</th>
                    <td><input type="password" autocomplete="off" name="externalPass" style="width: 25%;" value="${kwargs['externalPass']}" /></td>
                </tr>
                <tr>
                    <td colspan="2"><input id="authTypeEnt" type="radio" class="check" name="authType" value="entitlement"
                        py:attrs="{'checked': (kwargs['authType'] == 'entitlement') and 'checked' or None}" />
                        <label for="authTypeEnt">Use an entitlement</label>
                    </td>
                </tr>
                <tr>
                    <th style="padding-left: 3em; width: 25%;">Entitlement Key:</th>
                    <td>
                        <textarea rows="5" cols="50" name="externalEntKey"  py:content="kwargs['externalEntKey']" />
                    </td>
                </tr>
            </table>


            <h2>Mirror Settings</h2>
            <p>
                <div>
                    <input type="radio" class="radio" name="useMirror" value="none" id="useMirror_none"
                           py:attrs="{'checked': (kwargs['useMirror'] == 'none' or not kwargs['useMirror']) and 'checked' or None}" />
                    <label for="useMirror_none">
                        Cache contents of this repository locally as needed.
                        (Choose this option if you have a mirror preload disk supplied by rPath.)
                    </label>
                </div>
                <div>
                    <input type="radio" class="radio" name="useMirror" value="net" id="useMirror_net"
                            py:attrs="{'checked': kwargs['useMirror'] == 'net' and 'checked' or None}" />
                    <label for="useMirror_net">Mirror the contents of this repository over the network. (Requires authentication)</label>
                </div>
            </p>
            <table class="mainformhorizontal" id="mirrorSettings">
                <tr>
                   <th><em><label for="allLabels">Mirror All Labels on Repository:</label></em></th>
                   <td>
                       <input class="radio" type="checkbox" name="allLabels" value="1"
                            py:attrs="{'checked': kwargs['allLabels'] and 'checked' or None}" id="allLabels" />
                       <p class="help"><label for="allLabels">Check this box to mirror all of the labels
                            available in the source repository.</label></p>
                   </td>
                </tr>
                <tr>
                   <th><em>Additional labels to mirror:</em></th>
                   <td>
                       <input type="text" autocomplete="off" name="additionalLabelsToMirror" value="${kwargs['additionalLabelsToMirror']}" />
                       <p class="help">This should be a space-separated list of additional repository labels to mirror.</p>
                   </td>
                </tr>
            </table>
            <button py:if="not editing" class="img" type="submit">
                <img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add" />
            </button>
            <button py:if="editing" class="img" type="submit">
                <img src="${cfg.staticPath}/apps/mint/images/save_changes_button.png" alt="Save Changes" />
            </button>
            <input type="hidden" name="projectId" value="${projectId}" />
        </form>
        </div>
    </body>
</html>
