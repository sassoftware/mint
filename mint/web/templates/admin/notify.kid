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
        <a href="administer?operation=notify">User Notification</a>
    </div>

    <?python
        for var in ['extraMsg', 'subject', 'body']:
            kwargs[var] = kwargs.get(var, '')
        kwargs['errors'] = kwargs.get('errors', [])
    ?>

    <head>
        <title>${formatTitle('Notify All Users')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
              <p py:if="kwargs['extraMsg'] and not errors" class="message" py:content="kwargs['extraMsg']"/>
              <p py:if="kwargs['errors']" class="error">An Error Has Occurred</p>
              <p py:for="error in kwargs['errors']" class="errormessage" py:content="error"/>
              <h2>Notify All Users</h2>
              <p>Fields labeled with a <em class="required">red arrow</em> are required.  Note that the submission of this form may take several minutes, and will not ask for confirmation.  Be sure you are ready before hitting "Send"</p>
              <form action="administer" method="post">
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
                      <p class="help">Please type your message above.  It is suggested that you use another text editor (one with spell check capabilities) to compose your message, and then paste it below.</p>
                    </td>
                  </tr>
                </table>
                <p><button type="submit" name="operation" value="notify_send">Send</button></p>
              </form>
            </div>
        </td>
    </body>
</html>
