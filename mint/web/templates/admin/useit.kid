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
            <h3>Manage Use It Icons</h3>
            <p class="help">List icons and URLs to appear under "Use It." on the front page.</p>
            <p class="help">1 to 6 icons can be added at once.  If an icon is assigned to a spot that is already occupied, the older icon will be removed.  The other icons will remain unchanged.</p>  
            <form action="setIcons" method="post">
            <table width="100%">
                <tr>
                    <td>Icon 1 Filename:</td>
                    <td><input type="text" name="name1" size="30"/></td>
                    <td>Icon 1 URL:</td>
                    <td><input type="text" name="link1" size="30"/></td>
                </tr>
                <tr>
                    <td>Icon 2 Filename:</td>
                    <td><input type="text" name="name2" size="30"/></td>
                    <td>Icon 2 URL:</td>
                    <td><input type="text" name="link2" size="30"/></td>
                </tr>
                <tr>
                    <td>Icon 3 Filename:</td>
                    <td><input type="text" name="name3" size="30"/></td>
                    <td>Icon 3 URL:</td>
                    <td><input type="text" name="link3" size="30"/></td>
                </tr>
                <tr>
                    <td>Icon 4 Filename:</td>
                    <td><input type="text" name="name4" size="30"/></td>
                    <td>Icon 4 URL:</td>
                    <td><input type="text" name="link4" size="30"/></td>
                </tr>
                <tr>
                    <td>Icon 5 Filename:</td>
                    <td><input type="text" name="name5" size="30"/></td>
                    <td>Icon 5 URL:</td>
                    <td><input type="text" name="link5" size="30"/></td>
                </tr>
                <tr>
                    <td>Icon 6 Filename:</td>
                    <td><input type="text" name="name6" size="30"/></td>
                    <td>Icon 6 URL:</td>
                    <td><input type="text" name="link6" size="30"/></td>
                </tr>
                <tr>
                    <td colspan="2"><button name="op" value="set" type="submit">Add</button>
                    <button name="op" value="preview" type="submit">Preview</button></td>
                </tr>
            </table>
            </form>
            <br/>
            
            <div style="width: 720px; height: 334px;">
            <table py:if="table1Data" id="${table2Data and 'doubleTable' or 'singleTable'}">
                <tr>
                    <td id="useIt" py:for="td in table1Data">
                        ${td['itemId']}
                        <a href="${td['link']}"><img id="useitImg" src="${cfg.spotlightImagesDir}/${td['name']}" alt="${td['link']}"/></a><br/>
                        <a href="deleteUseItIcon?itemId=${td['itemId']}"><button>Delete</button></a>
                    </td>
                </tr>
            </table>
            <table id="doubleTable" py:if="table2Data">
                <tr>
                    <td id="useIt" py:for="td in table2Data">
                        ${td['itemId']}
                        <a href="${td['link']}"><img id="useitImg" src="${cfg.spotlightImagesDir}/${td['name']}" alt="${td['link']}"/></a><br/>
                        <a href="deleteUseItIcon?itemId=${td['itemId']}"><button>Delete</button></a>
                    </td>
                </tr>
            </table>
            </div>

                    
            <br/>
        </div>
    </body>
</html>
