<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
<?python
    from mint import userlevels

    isOwner = userLevel == userlevels.OWNER or auth.admin

    isRPL = project.external and project.getName() == 'rPath Linux'
?>
    <head>
        <title>${formatTitle('Mailing Lists: %s'%project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${buildsMenu(project.getBuilds(), isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>
            <div id="middle">
                <p class="message" py:for='msg in messages' py:content="msg"/>
                <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                <h2>Mailing Lists</h2>
                <div py:strip="True" py:if="isRPL">
                    <div class="mailingListButtons">
                        <h3>
                        <a href="http://lists.rpath.com/mailman/listinfo/distro-commits" target="_NEW">distro-commits</a></h3>
                        <p>Commits to the rPath Linux distribution repository.</p>
                        <ul>
                            <li>
                                <a href="http://lists.rpath.com/pipermail/distro-commits/" class="option" target="_NEW">Archives</a>
                            </li>
                        </ul>
                    </div>
                    <div class="mailingListButtons">
                        <h3>
                        <a href="http://lists.rpath.com/mailman/listinfo/distro-list" target="_NEW">distro-list</a></h3>
                        <p>rPath Linux Distribution Discussion.</p>
                        <ul>
                            <li>
                                <a href="http://lists.rpath.com/pipermail/distro-list/" class="option" target="_NEW">Archives</a>
                            </li>
                        </ul>

                        <div class="help">
                            <p>Click on the mailing list's name to receive more
                               more information about the mailing list,
                               including directions on how to subscribe or
                           unsubscribe.</p>
                        </div>
                    </div>
                </div>

                <div py:if="not isRPL" py:for="list in lists" class="mailingListButtons">
                    <h3><a href="${mailhost + 'listinfo/' + list.name}" target="_NEW">${list.name}</a></h3>
                    <p>${list.description}</p>

                    <ul>
                        <li><a href="${mailhost + '../pipermail/' + list.name}"
                                 class="option" target="_NEW">Archives</a>
                        </li>
                        <li py:if="auth.authorized">
                            <a class="option" href="subscribe?list=${list.name}">Subscribe</a>
                        </li>
                        <li py:if="not auth.authorized">
                            <a class="option" href="${mailhost + 'listinfo/' + list.name}">Subscribe</a>
                        </li>
                        <li py:if="isOwner">
                            <a href="${mailhost + 'admin/' + list.name}" class="option" target="_NEW">Admin Page</a>
                        </li>
                        <li py:if="auth.admin">
                            <a href="$basePath/deleteList?list=${list.name}" class="option">Delete List</a>
                        </li>
                        <li py:if="auth.admin">
                            <a href="$basePath/resetPassword?list=${list.name}" class="option">Request Password</a>
                        </li>
                    </ul>
                </div>
                <div py:if="not (lists or isRPL)">This project has no lists.</div>
                <h3 py:if="isOwner and not isRPL">Create a New Mailing List</h3>

                <form py:if="isOwner and not isRPL" name="createList" action="$basePath/createList" method="POST">
                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">List Name:</em></th>
                            <td>${hostname}-<input name="listname" type="text" /></td>
                        </tr>
                        <tr>
                            <th>List Description:</th>

                            <td><input name="description" type="text"/></td>
                        </tr>
                        <tr>
                            <th>List Password:</th>
                            <td><input name="listpw" type="password"/>
                                <p class="help">
                                    If you leave both password fields blank, a random password
                                    will be generated and e-mailed to all project owners.
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <th>List Password<br/>(again):</th>
                            <td><input name="listpw2" type="password"/></td>
                        </tr>
                    </table>
                    <p><button type="submit">Create List</button></p>
                </form>
            </div>
        </div>
    </body>
</html>
