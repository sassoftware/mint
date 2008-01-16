<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint.web.templatesupport import projectText
    for var in ['outboundMirrorId', 'mirrorUser', 'mirrorPass', 'targetUrl']:
        kwargs[var] = kwargs.get(var, '')
?>
    <head>
        <title>${formatTitle('Add Outbound Mirror')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <form action="${cfg.basePath}admin/processAddOutboundMirrorTarget" method="post">
                <h2>Add Outbound Mirror Target</h2>

                <p>Adding an outbound mirror target for <span style="font-weight: bold;">${projectName}</span>. <span py:strip="True" py:if="targets">This ${projectText().lower()} is configured to mirror to the following repositories:<ul><li py:for="target in targets">${target}</li></ul></span></p>

                <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
                    <tr>
                        <th><em class="required">Target Update Service</em></th>
                        <td>
                            <input type="text" name="targetUrl" maxlength="255" value="${kwargs['targetUrl']}"/>
                            <p class="help">Use the fully-qualified domain name of the target repository or Update Service (example: mirror.rpath.com).</p>
                        </td>
                    </tr>
                    <tr>
                        <th><em class="required">Update Service Username:</em></th>
                        <td><input type="text" name="mirrorUser" style="width: 25%;" value="${kwargs['mirrorUser']}" /></td>
                    </tr>
                    <tr>
                        <th><em class="required">Update Service Password:</em></th>
                        <td><input autocomplete="off" type="password" name="mirrorPass" style="width: 25%;" value="${kwargs['mirrorPass']}" /></td>
                    </tr>
                </table>
                <button class="img" type="submit">
                    <img src="${cfg.staticPath}/apps/mint/images/add_button.png" alt="Add Target" />
                </button>
                <input type="hidden" name="outboundMirrorId" value="${outboundMirrorId}" />
            </form>
        </div>
    </body>
</html>
