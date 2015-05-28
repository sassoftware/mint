<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
-->

<?python
    from mint.web.templatesupport import projectText
    for var in ['name', 'hostname', 'label', 'url',
        'externalUser', 'externalPass', 'externalEntKey',
        'authType', 'useMirror',
        'externalAuth', 'authType', 'additionalLabelsToMirror',
        'allLabels', 'backupExternal', 'backgroundMirror']:
        kwargs[var] = kwargs.get(var, initialKwargs.get(var, ''))
?>
    <head>
        <title>${formatTitle((editing and 'Edit' or 'Add') + ' External %s'%projectText().title())}</title>
    </head>
    <body>
    <div class="admin-page">
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="admin-spanright">
          <form action="${cfg.basePath}admin/processAddExternal" method="post">
            <div class="page-title-no-project">${editing and 'Edit ' or 'Add '} External ${projectText().title()}</div>
            <p py:if="not editing" class="help">External ${projectText().lower()}s appear just like the
            ${projectText().lower()}s you host on ${cfg.productName} with one exception:
            the repository is <em>not</em> stored on
            ${cfg.productName}.  External ${projectText().lower()}s are useful for
            integrating the contents of another organization's
            repository into ${cfg.productName}, making it easier for
            your users to reference that organization's work in
            theirs.</p>

            <table class="mainformhorizontal">
            <tr>
                  <td class="form-label"><em class="required">${projectText().title()} Title:</em></td>
                  <td>
                    <input type="text" autocomplete="off" name="name" value="${kwargs['name']}"/>
                    <p class="help">Enter a description for this
                    ${projectText().lower()}. To reduce confusion, we recommend
                   that you enter the external ${projectText().lower()}'s title.</p>
                  </td>
            </tr>
            <tr>
                <td class="form-label"><em py:strip="editing" class="required">${projectText().title()} Short Name:</em></td>
                <td py:if="editing" class="form-label">
                    ${kwargs['hostname']}<input type="${editing and 'hidden' or 'text'}" autocomplete="off" name="hostname" maxlength="16" value="${kwargs['hostname']}"/>
                </td>
                <td py:if="not editing">
                    <input type="${editing and 'hidden' or 'text'}" autocomplete="off" name="hostname" maxlength="16" value="${kwargs['hostname']}"/>
                    <p class="help">Enter a name for this
                    ${projectText().lower()}.
                    It must start with a letter and contain only letters and
                    numbers, and be less than or equal to 16 characters
                    long. To reduce confusion, we recommend
                    that you enter the external ${projectText().lower()}'s short name.</p>
                </td>
            </tr>
            <tr>
                <td class="form-label"><em class="required">${projectText().title()} Label:</em></td>
                <td>
                  <input type="text" autocomplete="off" name="label" value="${kwargs['label']}" />
                  <p class="help">Enter this ${projectText().lower()}'s label.</p>
                </td>
            </tr>
            <tr>
                <td class="form-label">Repository URL:</td>
                <td>
                  <input type="text" autocomplete="off" name="url" value="${kwargs['url']}"/>
                  <p class="help">Enter the URL for this ${projectText().lower()}'s
                  repository.  If a URL is not provided, the standard
                  URL format will be derived from the ${projectText().lower()}'s label.</p>
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
                <td class="form-label" style="text-align: right;">Username:</td>
                <td width="100%"><input type="text" autocomplete="off" name="externalUser" style="width: 25%;" value="${kwargs['externalUser']}" /></td>
            </tr>
            <tr>
                <td class="form-label" style="text-align: right;">Password:</td>
                <td><input type="password" autocomplete="off" name="externalPass" style="width: 25%;" value="${kwargs['externalPass']}" /></td>
            </tr>
            <tr>
                <td colspan="2"><input id="authTypeEnt" type="radio" class="check" name="authType" value="entitlement"
                    py:attrs="{'checked': (kwargs['authType'] == 'entitlement') and 'checked' or None}" />
                    <label for="authTypeEnt">Use an entitlement</label>
                </td>
            </tr>
            <tr>
                <td class="form-label" style="text-align: right;">Entitlement Key:</td>
                <td>
                    <textarea rows="5" cols="50" name="externalEntKey"  py:content="kwargs['externalEntKey']" />
                </td>
            </tr>
            </table>


            <h2>Mirror Settings</h2>
            <table class="mainformhorizontal" id="mirrorSettings">
            <tr>
                <td><input type="radio" class="radio" name="useMirror" value="none" id="useMirror_none"
                       py:attrs="{'checked': (kwargs['useMirror'] == 'none' or not kwargs['useMirror']) and 'checked' or None}" /></td>
                <td><label for="useMirror_none">
                    Cache contents of this repository locally as needed. (This is the recommended setting.)</label>
                </td>
            </tr>
            <tr>
                <td><input type="radio" class="radio" name="useMirror" value="net" id="useMirror_net"
                        py:attrs="{'checked': kwargs['useMirror'] == 'net' and 'checked' or None}" /></td>
                <td>
                <label for="useMirror_net">Mirror the contents of this repository over the network. (Requires authentication.)</label></td>
            </tr>
            <tr>
                <td width="22"><input type="checkbox" id="backgroundMirror" name="backgroundMirror" value="1"
                        py:attrs="{'checked': kwargs['backgroundMirror'] and 'checked' or None}" /></td>
                <td><label>Run in cached mode until the mirror completes</label></td>
            </tr>
            <tr>
               <td><input class="radio" type="checkbox" name="allLabels" value="1"
                        py:attrs="{'checked': kwargs['allLabels'] and 'checked' or None}" id="allLabels" /></td>
               <td>
                   <label for="allLabels">Mirror All Labels on Repository</label>
                   <p class="help"><label for="allLabels">Check this box to mirror all of the labels
                        available in the source repository.</label></p>
               </td>
            </tr>
            </table>
            <table class="mainformhorizontal" id="moreMirrorSettings">
            <tr>
               <td class="form-label"><em>Additional labels to mirror:</em></td>
               <td width="100%">
                   <input type="text" autocomplete="off" name="additionalLabelsToMirror" value="${kwargs['additionalLabelsToMirror']}" />
                   <p class="help">This should be a space-separated list of additional repository labels to mirror.</p>
               </td>
            </tr>
            </table>

            <h2>Backup Settings</h2>
            <table class="mainformhorizontal" id="mirrorSettings">
            <tr>
                <td width="22"><input type="checkbox" id="backupExternal" name="backupExternal" value="1"
                        py:attrs="{'checked': kwargs['backupExternal'] and 'checked' or None}" /></td>
                <td><label>Backup inbound mirror contents. (This will make backups substantially larger.)</label></td>
            </tr>
            </table>
            <br />
            <p class="p-button">
            <button py:if="not editing" class="img" type="submit">
                <img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add" />
            </button>
            <button py:if="editing" class="img" type="submit">
                <img src="${cfg.staticPath}/apps/mint/images/save_changes_button.png" alt="Save Changes" />
            </button>
            <input type="hidden" name="projectId" value="${projectId}" />
            </p>
            <br />
        </form>
        </div>
        <div class="bottom"/>
    </div>
    </body>
</html>
