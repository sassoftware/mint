<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
<?python #dummy
    from mint import userlevels

    isOwner = userLevel == userlevels.OWNER or auth.admin
?>
    <head>
        <title>${formatTitle('Mailing Lists: %s'%project.getName())}</title>
    </head>

    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Mailing Lists</a>
    </div>

    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>
        </td>
        <td id="main">
            <div class="pad">
                <p class="message" py:for='msg in messages' py:content="msg"/>
                <h2>${project.getName()}<br />Mailing Lists</h2>
                <div py:for="list in lists">
                    <h3><a href="${mailhost + 'listinfo/' + list.name}" target="_NEW">${list.name}</a></h3>
                    <p>${list.description}</p>
                    <div style="float:left; margin-right:5px;">
                        <span><a href="${mailhost + '../pipermail/' + list.name}"
                                 class="option" target="_NEW">Archives</a>
                        </span>
                    </div>
                    <div style="float:left; margin-right:5px;">
                        <span py:if="auth.authorized">
                            <a class="option" href="subscribe?list=${list.name}">Subscribe</a>
                        </span>
                    </div>
                    <div style="float:left; margin-right:5px;">
                        <span py:if="not auth.authorized">
                            <a class="option" href="${mailhost + 'listinfo/' + list.name}">Subscribe</a>
                        </span>
                    </div>

                    <div style="float:left; margin-right:5px;">
                        <span py:if="isOwner">
                            <a href="${mailhost + 'admin/' + list.name}" class="option" target="_NEW">Admin Page</a>
                        </span>
                    </div>

                    <div style="float:left; margin-right:5px;">
                        <span py:if="auth.admin">
                            <a href="$basePath/deleteList?list=${list.name}" class="option">Delete List</a>
                        </span>
                    </div>
                    &#160;
                    <br clear="all"/>
                    &#160;
                </div>
                <div py:if="not lists">This project has no lists.</div>
                
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
        </td>
        ${projectsPane()}
    </body>
</html>
