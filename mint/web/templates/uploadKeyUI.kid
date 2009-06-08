<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
from mint.web.templatesupport import projectText
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layoutUI.kid'">
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
        <div class="fullpage">
            <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
            <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
            <div id="right" class="side">
            </div>
            <div id="leftcenter">
                <div class="page-title-no-project">
                    Upload a Package Signing Key
                </div>

                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="processKey">

                <table class="mainformhorizontal">
                <tr>
                        <td class="form-label"><em class="required">Select ${projectText().title()}s:</em></td>
                        <td>
                             <select class="key-project-list" multiple="multiple" size="10" name="projects">
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
                        <td class="form-label"><em class="required">Public Key:</em></td>
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
                <p class="p-button">
                    <button id="uploadKeySubmit" class="img" type="submit">
                        <img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" />
                    </button>
                </p>
            </form>
        </div><br class="clear"/>
        <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
        <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
        <div class="bottom"/>
    </div>
    </body>
</html>
