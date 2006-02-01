<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Upload a Key</a>
    </div>
    <?python
        for var in ['keydata']:
            kwargs[var] = kwargs.get(var, '')
        kwargs['projects'] = kwargs.get('projects', [])
    ?>
    <head>
        <title>${formatTitle('Upload a Key')}</title>
    </head>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <p py:if="errors" class="error">Key Upload Error${len(errors) > 1 and 's' or ''}</p>
                <p py:for="error in errors" class="errormessage" py:content="error"/>
                <h2>Upload a Package Signing Key</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="processKey">

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Project or Projects:</em></th>
                            <td>
                                 <select class="wide" multiple="multiple" size="10" name="projects">
                                    <option py:for="project, level in [(x[0], x[1]) for x in projectList if x[1] in userlevels.WRITERS]" py:content="project.getName()" value="${project.getHostname()}"/>
                                 </select>
                                 <p class="help">Select one or more projects to which to upload this key.  To select multiple projects, hold down your keyboard's Ctrl key while clicking.<b>This key can never be deleted from the repository to which you submit it, so choose carefully.</b></p>
                            </td>
                        </tr>

                        <tr>
                            <th><em class="required">Public Key:</em></th>
                            <td>
                                <textarea rows="15" type="text" name="keydata" py:content="kwargs['keydata']" />

                                <p class="help">Insert your PGP or GnuPG Public Key here in ascii format.  Paste only one key at a time.  Please only submit your own public keys.  Once a key is submitted, it cannot be removed.</p>
                                <p class="help">For help generating a PGP key, visit <a href="http://webber.dewinter.com/gnupg_howto/english/GPGMiniHowto-3.html#ss3.1">here</a></p>
                                <p class="help">For help getting the public key in a format suitable for pasting, click <a href="http://webber.dewinter.com/gnupg_howto/english/GPGMiniHowto-3.html#ss3.2">here</a></p>
                            </td>
                        </tr>
                    </table>
                    <p><button class="img" type="submit"><img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" /></button></p>
                </form>
            </div>
        </td>
    </body>
</html>
