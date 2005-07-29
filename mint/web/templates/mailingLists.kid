<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head/>
    <?python # this comment has to be here if the first line is an import...weird!
        from mint import userlevels

        isOwner = userLevel == userlevels.OWNER
    ?>

    <div py:def="breadcrumb()" class="pad">
        You are here:
        <a href="#">rpath</a>
        <a href="../">${project.getName()}</a>
        <a href="#">Releases </a>
    </div>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()} Mailing Lists</h2>
                <div py:for="list in lists">
                    <p><a href="${mailhost + 'listinfo/' + list.name}" target="_NEW" py:content="list.name"/></p>
                    <p py:content="list.description"/>
                    <span><a href="${mailhost + '../pipermail/' + list.name}" target="_NEW">Archives</a></span>
                    <span py:if="auth.authorized and not isOwner"><a href="subscribe?list=${list.name}">Subscribe</a></span>
                    <span py:if="isOwner"><a href="${mailhost + 'admin/' + list.name}" target="_NEW">Administration Page</a></span>
                    <span py:if="isOwner"><a href="deleteList?list=${list.name}">Delete List</a></span>
                </div>
                <h2 py:if="isOwner">Create a New Mailing List</h2>
                <form py:if="isOwner" name="createList" action="createList" method="POST">
                    <table border="0" cellspacing="0" cellpadding="0" class="mai
nformhorizontal">
                    <tr>
                        <th><em class="required">List Name:</em></th>
                        <td>${project.getName()}-<input name="listname" type="text" /></td>
                    </tr>
                    <tr>
                        <th>List Description:</th>
                        <td><input name="description" type="text"/></td>
                    </tr>
                    <tr>
                        <th>List Password:</th>
                        <td><input name="listpw" type="password"/>
                            <p class="help">If you leave both password fields blank, a random password will be generated and e-mailed to all project owners.</p>
                        </td>
                    </tr>
                    <tr>
                        <th>List Password (again):</th>
                        <td><input name="listpw2" type="password"/></td>
                    </tr>
                </table>
                <button type="submit">Create List</button>
                </form>
            </div>
        </td>
        ${projectsPane()}
    </body>
</html>
