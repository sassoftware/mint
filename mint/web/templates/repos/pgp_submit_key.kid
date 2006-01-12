<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">

    <!-- table of pgp keys -->
    <head>
      <title>${formatTitle('Upload PGP Key: %s' % project.getNameForDisplay())}</title>
    </head>
    <body>
        <td id="left" class="side">
          <div class="pad">
            <h2>PGP Key Submission</h2>
              <form method="POST" action="submitPGPKey">
                <table class="mainformhorizontal" id="users">
               	  <tbody>
                    <tr>
                        <td><em class="required">Paste PGP Key Here</em></td>
                        <td witdh="100%">
                          <textarea name="keyData" rows="40" cols="80"/>
                            <p class="help">* Submit only one key at a time</p>
                            <p class="help">* Submit ONLY your own public keys</p>
                            <p class="help">* Once a key is submitted it CANNOT be removed</p>
                        </td>
                    </tr>
                  </tbody>
                </table>
                <p><button type="submit">Submit Key</button></p>
              </form>
          </div>
        </td>
    </body>
</html>
