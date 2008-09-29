<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2008 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Administer')}</title>
    </head>
    <?python # kid bug requires comment.
        from mint import maintenance
        from mint.web.templatesupport import projectText
    ?>
    <body>
        <div class="admin-page">
            <div id="left" class="side">
                ${adminResourcesMenu()}
            </div>
            <div id="admin-spanright">
                <div class="page-title-no-project">Manage Front Page Selections</div>
                
                <p>
                <form action="addSelection" method="post">
                <table class="mainformhorizonal">
                <tr>
                    <td class="form-label">${projectText().title()} Name:</td>
                    <td width="100%"><input type="text" name="name" size="50"/></td>
                </tr>
                <tr>
                    <td class="form-label">URL:</td>
                    <td><input type="text" name="link" size="50"/></td>
                </tr>
                <tr>
                    <td class="form-label">Rank: </td>
                    <td><input type="text" name="rank" size="10"/>
                    <p class="help">(Items are listed in order of rank, from low to high)</p></td>
                </tr>
                <tr>
                    <td/>
                    <td><button name="op" value="add" type="submit">Add</button></td>
                </tr>
                </table>
                </form>
                </p>
                <p>
                <table class="mainformhorizonal" py:if="selectionData">
                <tr>
                    <th>${projectText().title()} Name</th>
                    <th>URL</th>
                    <th>Rank</th>
                    <th>Remove</th>
                </tr>
                <?python rowStyle = 0 ?>
                <tr py:for="item in selectionData" class="${rowStyle and 'odd' or ''}">
                    <td>${item['name']}</td>
                    <td>${item['link']}</td>
                    <td>${item['rank']}</td>
                    <td><a href="${cfg.basePath}admin/deleteSelection?itemId=${item['itemId']}">x</a></td>
                    <?python rowStyle ^= 1 ?>
                </tr>
                </table>
                </p>
            </div>
            <div class="bottom"/>
        </div>
    </body>
</html>
