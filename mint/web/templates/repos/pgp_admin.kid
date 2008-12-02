<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">

    <div py:def="breadcrumb" py:strip="True">
        <a href="${cfg.basePath}project/${project.getHostname()}/">${project.getNameForDisplay()}</a>
        <a href="#">PGP Key Browser</a>
    </div>

    <div py:def="generateOwnerListForm(fingerprint, users, username = None)" py:strip="True">
      <form action="pgpChangeOwner" method="post">
        <input type="hidden" name="key" value="${fingerprint}"/>
        <select name="owner">
            <option py:for="userName in [x for x in sorted(users) if x not in ('anonymous', cfg.authUser)]" value="${userName}"
                    py:attrs="{'selected': (userName==username) and 'selected' or None}"
                    py:content="userName" />
        </select>
        <button class="img" id="pgpChangeOwner" type="submit"><img src="${cfg.staticPath}/apps/mint/images/change_owner_button.png" alt="Change Owner" /></button>
      </form>
    </div>

    <div py:def="breakKey(key)" py:strip="True">
        <?python
    brokenkey = ''
    for x in range(len(key)/4):
        brokenkey += key[x*4:x*4+4] + " "
        ?>
        ${brokenkey}
    </div>

    <div py:def="printKeyTableEntry(keyEntry, userName)" py:strip="True">
     <tr class="key-ids">
      <td>
        <div>pub: ${breakKey(keyEntry['fingerprint'])}</div>
        <div py:for="id in keyEntry['uids']"> uid: &#160; &#160; ${id}</div>
        <div py:for="subKey in keyEntry['subKeys']">sub: ${breakKey(subKey)}</div>
      </td>
      <td py:if="auth.admin">${generateOwnerListForm(keyEntry['fingerprint'], users, userName)}</td>
     </tr>
    </div>

    <!-- table of pgp keys -->
    <head>
        <title>${formatTitle('PGP Keys: %s' % project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            
            <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                <div id="right" class="side">
                    ${resourcePane()}
                    ${builderPane()}
                </div>
                <div id="middle">
              
                    <h1>${project.getNameForDisplay(maxWordLen = 30)}</h1>
                    <div class="page-title">${admin and "All " or "My "}PGP Keys</div>
                    NOTE: Keys owned by '--Nobody--' may not be used to sign troves.
                    These keys are, for all intents and purposes, disabled.
                    <p>
                    <table class="results" id="users">
                    <thead>
                        <tr>
                            <td>Key</td>
                            <td py:if="auth.admin">Owner</td>
                        </tr>
                    </thead>
                    <tbody>
                        <div py:for="userName in sorted(users)" py:strip="True">
                          <div py:for="keyEntry in openPgpKeys[userName]" py:strip="True">
                              ${printKeyTableEntry(keyEntry, userName)}
                          </div>
                        </div>
                    </tbody>
                    </table>
                    </p>
                </div>
                <br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>
