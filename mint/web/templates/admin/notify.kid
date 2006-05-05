<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <?python
        for var in ['extraMsg', 'subject', 'body']:
            kwargs[var] = kwargs.get(var, '')
        kwargs['errors'] = kwargs.get('errors', [])
    ?>

    <head>
        <title>${formatTitle('Notify All Users')}</title>
    </head>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
          <h2>Notify All Users</h2>
          <p>Fields labeled with a <em class="required">red arrow</em> are required.
            Note that the submission of this form may take several minutes, and will
            not ask for confirmation.  Be sure you are ready before hitting "Send".
          </p>
          <form action="${cfg.basePath}admin/sendNotify" method="post">
            <table cellpadding="0" border="0" cellspacing="0" class="mainformhorizontal">
              <tr>
                <th><em class="required">Message Subject:</em></th>
                <td>
                  <input type="text" name="subject" value="${kwargs['subject']}"/>
                </td>
              </tr>
              <tr>
                <th><em class="required">Message Body:</em></th>
                <td>
                  <textarea rows="12" name="body" py:content="kwargs['body']"/>
                  <p class="help">
                    Please type your message above.  It is suggested that you use
                    another text editor (one with spell check capabilities) to
                    compose your message, and then paste it above.
                  </p>
                </td>
              </tr>
            </table>
            <p><button type="submit" name="operation" value="notify_send">Send</button></p>
          </form>
        </div>
    </body>
</html>
