<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../project.kid', '../layout.kid'">

    <div py:def="breadcrumb" py:strip="True">
        <a href="${cfg.basePath}project/${project.getHostname()}/">${project.getName()}</a>
        <a href="#">PGP Key Browser</a>
    </div>

    <div py:def="generateOwnerListForm(fingerprint, users, userid = None)" py:strip="True">
      <form action="pgpChangeOwner" method="post">
        <input type="hidden" name="key" value="${fingerprint}"/>
        <select name="owner">
            <option value="${None}">--Nobody--</option>
            <option py:for="userId, userName in users.items()" value="${userName}"
                    py:attrs="{'selected': (userId==userid) and 'selected' or None}"
                    py:content="userName" />
        </select>
        <button type="submit" value="Change">Change Owner</button>
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

    <div py:def="printKeyTableEntry(key, userId)" py:strip="True">
     <tr class="key-ids">
      <td>
        <div>pub: ${breakKey(key)}</div>
        <div py:for="id in keyTable.getUserIds(key)"> uid: &#160; &#160; ${id}</div>
        <div py:for="subkey in keyTable.getSubkeys(key)">sub: ${breakKey(subkey)}</div>
      </td>
      <td py:if="admin" style="text-align: right;">${generateOwnerListForm(key, users, userId)}</td>
     </tr>
    </div>

    <!-- table of pgp keys -->
    <head>
        <title>${formatTitle('PGP Keys: %s' % project.getName())}</title>
    </head>
    <body>
        <td id="main" class="spanall">
          <div class="pad">
            <h2>${admin and "All " or "My "}PGP Keys</h2>
            NOTE: Keys owned by '--Nobody--' may not be used to sign troves.
            These keys are, for all intents and purposes, disabled.
            <table class="results" id="users">
                <thead>
                    <tr>
                        <td>Key</td>
                        <td py:if="admin" style="text-align: right;">Owner</td>
                    </tr>
                </thead>
                <tbody>
                    <div py:for="key in keyTable.getUsersMainKeys(None)" py:strip="True">
                      ${printKeyTableEntry(key, None)}
                    </div>
                    <div py:for="userId, userName in users.items()" py:strip="True">
                      <div py:for="key in keyTable.getUsersMainKeys(userId)" py:strip="True">
                          ${printKeyTableEntry(key, userId)}
                      </div>
                    </div>
                </tbody>
            </table>
            <p><a href="pgpNewKeyForm">Add or Update a Key</a></p>
          </div>

        </td>
    </body>
</html>
