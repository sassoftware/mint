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
        import time
    ?>
    <body>
        <div id="left" class="side">
            ${adminResourcesMenu()}
        </div>
        <div id="spanright">
            <h3>Manage Spotlight Appliances</h3>
            <table id="spotTable" py:if="spotlightData">
                <thead>
                <tr>
                    <th id="spotTh">Appliance Name</th>
                    <th id="spotTh">Start Date</th>
                    <th id="spotTh">End Date</th>
                    <th id="spotTh">Options</th>
                </tr>
                </thead>
                <tbody>
                <?python rowStyle = 0 ?>
                <tr py:for="item in spotlightData" class="${rowStyle and 'odd' or ''}">
                    <td id="spotTd">${item['title']}</td>
                    <td id="spotTd">${time.strftime("%m/%d/%Y", time.localtime(item['startDate']))}</td>
                    <td id="spotTd">${time.strftime("%m/%d/%Y", time.localtime(item['endDate']))}</td>
                    <td id="spotTd"><form action="preview" method="post"><input py:for="k, v in item.iteritems()" type="hidden" name="${k}" value="${v}"/><button type="submit" >Preview</button><a href="${cfg.basePath}admin/deleteSpotlightItem?itemId=${item['itemId']}&#038;title=${item['title']}"><button>Delete</button></a></form></td>
                    <?python rowStyle ^= 1 ?>
                </tr>
                </tbody>
            </table>
        
            <h4 onclick="javascript:toggle_display('file_help');" style="cursor: pointer;">Add a New Appliance Spotlight &nbsp;<img id="file_help_expander" src="${cfg.staticPath}/apps/mint/images/BUTTON_expand.gif" class="noborder" /></h4>
            <div id="file_help" style="display: none;  border: 1px solid #CCC; padding-bottom: 30px; padding-right: 5px; background-color: #eee;">
            <form action="${cfg.basePath}admin/addSpotlightItem" method="post" enctype="multipart/form-data">
            <table>
                <tr>
                    <td id="spotLabel">Appliance Name:</td>
                    <td id="spotInput"><input type="text" size="50" name="title"/></td>
                </tr>
                <tr>
                    <td id="spotLabel"><label>Appliance Text:</label></td>
                    <td id="spotInput"><textarea cols="50" rows="4" class="spotlightInput" name="text"/></td>
                </tr>
                <tr>
                    <td id="spotLabel"><label>Project URL:</label></td>
                    <td id="spotInput"><input size="50" type="text" name="link"/></td>
                </tr>
                <tr>
                    <td id="spotLabel"><label>Appliance Logo (Enter file name.  Leave blank for none.):</label></td>
                    <td id="spotInput"><input type="text" size="50" name="logo"/></td>
                </tr>
                <tr>
                    <td id="spotLabel"><label>Start Date (mm/dd/yyyy):</label></td>
                    <td id="spotInput"><input type="text" size="20" name="startDate"/></td>
                </tr>
                <tr>
                    <td id="spotLabel"><label>End Date (mm/dd/yyyy):</label></td>
                    <td id="spotInput"><input type="text" size="20" name="endDate"/></td>
                </tr>
                <tr>
                    <td id="spotLabel"><label>Show "Spotlight Archive" link?</label></td>
                    <td id="spotInput"><input type="radio" name="showArchive" value="1"/>Yes<input type="radio" name="showArchive" checked="true" value="0"/>No</td>
                </tr>
            </table>
                <button style="float: right; margin-bottom: 10px;" type="submit" name="operation" value="apply">Apply</button> 
                <button style="float: right; margin-bottom: 10px;" name="operation" value="preview" type="submit">Preview</button> 
            </form>
            </div>
            
        </div>
    </body>
</html>
