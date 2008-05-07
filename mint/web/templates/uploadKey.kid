<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <?python
        for var in ['keydata']:
            kwargs[var] = kwargs.get(var, '')
        kwargs['projects'] = kwargs.get('projects', [])
    ?>
    <head>
        <title>${formatTitle('Upload a Key')}</title>
    </head>
    <body>
        <div id="layout">
            <h2>Upload a Package Signing Key</h2>
            <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
            <form method="post" action="processKey">

                <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                    <tr>
                        <th><em class="required">${projectText().title()} or ${projectText().title()}s:</em></th>
                        <td>
                             <select class="wide" multiple="multiple" size="10" name="projects">
                                <option py:for="project, hostname in projects"
                                    py:content="project"
                                    py:attrs="(hostname in kwargs['projects']) and {'selected': 'selected'} or {}"
                                    value="${hostname}"/>
                             </select>
                             <p class="help">
                                Select one or more ${projectText().lower()}s to which to upload this key.
                                To select multiple ${projectText().lower()}s, hold down your keyboard's
                                Ctrl key while clicking. <strong>This key can never be 
                                deleted from the repository to which you submit it, so 
                                choose carefully.</strong>
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <th><em class="required">Public Key:</em></th>
                        <td>
                            <textarea rows="15" type="text" name="keydata" py:content="kwargs['keydata']" />

                            <p class="help">
                                Insert your PGP or GnuPG Public Key here in ascii format.
                                Paste only one key at a time.  Please only submit your own
                                public keys.  Once a key is submitted, it cannot be removed.
                            </p>
                            <p class="help">
                                For help generating a PGP key, visit 
                                <a href="http://webber.dewinter.com/gnupg_howto/english/GPGMiniHowto-3.html#ss3.1">here</a>
                            </p>
                            <p class="help">
                                For help getting the public key in a format suitable for pasting, click 
                                <a href="http://webber.dewinter.com/gnupg_howto/english/GPGMiniHowto-3.html#ss3.2">here</a>
                            </p>
                        </td>
                    </tr>
                </table>
                <p>
                    <button id="uploadKeySubmit" class="img" type="submit">
                        <img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" />
                    </button>
                </p>
            </form>
        </div>
    </body>
</html>
