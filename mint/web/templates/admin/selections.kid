<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid', 'admin.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Administer')}</title>
    </head>
    <?python # kid bug requires comment.
        from mint import maintenance
    ?>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <h3>Manage Front Page Selections</h3>
            <form action="addSelection" method="post">
            <table>
                <tr>
                    <td>Project Name:</td>
                    <td width="75%"><input type="text" name="name" size="50"/></td>
                </tr>
                <tr>
                    <td>URL:</td>
                    <td><input type="text" name="link" size="50"/></td>
                </tr>
                <tr>
                    <td>Rank: (Items are listed in order of rank, from low to high)</td>
                    <td><input type="text" name="rank" size="10"/></td>
                </tr>
                <tr>
                    <td/>
                    <td><button name="op" value="add" type="submit">Add</button>
                    <button name="op" value="preview" type="submit">Preview</button></td>
                </tr>
            </table>
            </form>
            <br/>

            <table id="spotTable" style="width: 100%;" py:if="selectionData">
                <thead>
                <tr>
                    <th id="spotTh">Project Name</th>
                    <th id="spotTh">URL</th>
                    <th id="spotTh">Rank</th>
                    <th id="spotTh">Options</th>
                </tr>
                </thead>
                <tbody>
                <?python rowStyle = 0 ?>
                <tr py:for="item in selectionData" class="${rowStyle and 'odd' or ''}">
                    <td id="spotTd">${item['name']}</td>
                    <td id="spotTd">${item['link']}</td>
                    <td id="spotTd">${item['rank']}</td>
                    <td id="spotTd"><a href="${cfg.basePath}admin/deleteSelection?itemId=${item['itemId']}">Delete</a></td>
                    <?python rowStyle ^= 1 ?>
                </tr>
                </tbody>
            </table>
            <br/>
        </div>
    </body>
</html>
