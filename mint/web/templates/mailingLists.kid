<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
<?python
    isRPL = project.external and project.getName() == 'rPath Linux'
?>
    <head>
        <title>${formatTitle('Mailing Lists: %s'%project.getNameForDisplay())}</title>
    </head>

    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(projectPublishedReleases, isOwner)}
                ${commitsMenu(projectCommits)}
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
                        <li py:if="isOwner">
                            <a href="${mailhost + 'admin/' + list.name}" class="option" target="_NEW">Admin Page</a>
                        </li>
                        <li py:if="isOwner">
                            <a href="$basePath/deleteList?list=${list.name}" class="option">Delete List</a>
                        </li>
                        <li py:if="isOwner">
                            <a href="$basePath/resetPassword?list=${list.name}" class="option">Request Password</a>
                        </li>
                    </ul>
                </div>
                <div py:if="not (lists or isRPL)">This project has no lists.</div>
            </div>
        </div>
    </body>
</html>
