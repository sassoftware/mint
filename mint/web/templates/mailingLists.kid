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
                ${releasesMenu(project.getReleases(), isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="right" class="side">
                ${resourcePane()}
                ${groupTroveBuilder()}
            </div>
            <div class="middle">
                <p class="message" py:for='msg in messages' py:content="msg"/>
                <h2>${project.getNameForDisplay(maxWordLen = 50)}<br />Mailing Lists</h2>
                <div py:strip="True" py:if="isRPL">
                    <h3>
                    <a href="http://lists.rpath.com/mailman/listinfo/distro-commits" target="_NEW">distro-commits</a></h3>
                    <p>Commits to the rPath Linux distribution repository.</p>
                    <div style="float:left; margin-right:5px;">
                        <span>
                        <a href="http://lists.rpath.com/pipermail/distro-commits/" class="option" target="_NEW">Archives</a>
                        </span>
                    </div>

                    <br clear="all" />

                    <h3>
                    <a href="http://lists.rpath.com/mailman/listinfo/distro-list" target="_NEW">distro-list</a></h3>
                    <p>rPath Linux Distribution Discussion.</p>
                    <div style="float:left; margin-right:5px;">
                        <span>
                        <a href="http://lists.rpath.com/pipermail/distro-list/" class="option" target="_NEW">Archives</a>
                        </span>
                    </div>

                    <br clear="all" />

                    <div class="help" style="margin-top: 1em;">
                        <p>Click on the mailing list's name to receive more
                           more information about the mailing list,
                           including directions on how to subscribe or
                           unsubscribe.</p>
                    </div>

                </div>

                <div py:if="not isRPL" py:for="list in lists" id="mailingListButtons">
                    <h3><a href="${mailhost + 'listinfo/' + list.name}" target="_NEW">${list.name}</a></h3>
                    <p>${list.description}</p>
                    <div>
                        <span><a href="${mailhost + '../pipermail/' + list.name}"
                                 class="option" target="_NEW">Archives</a>
                        </span>
                    </div>
                    <div>
                        <span py:if="auth.authorized">
                            <a class="option" href="subscribe?list=${list.name}">Subscribe</a>
                        </span>
                    </div>
                    <div>
                        <span py:if="not auth.authorized">
                            <a class="option" href="${mailhost + 'listinfo/' + list.name}">Subscribe</a>
                        </span>
                    </div>

                    <div>
                        <span py:if="isOwner">
                            <a href="${mailhost + 'admin/' + list.name}" class="option" target="_NEW">Admin Page</a>
                        </span>
                    </div>

                    <div>
                        <span py:if="auth.admin">
                            <a href="$basePath/deleteList?list=${list.name}" class="option">Delete List</a>
                        </span>
                    </div>

                    <div>
                        <span py:if="auth.admin">
                            <a href="$basePath/resetPassword?list=${list.name}" class="option">Request Password</a>
                        </span>
                    </div>
                </div>
                <div py:if="not (lists or isRPL)">This project has no lists.</div>
                <h2 py:if="isOwner">Create a New Mailing List</h2>

                <form py:if="isOwner" name="createList" action="$basePath/createList" method="POST">
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
