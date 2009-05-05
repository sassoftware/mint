<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
?>
    <!-- creates a selection dropdown based on a list -->
    <select py:def="makeSelect(elementName, items, selected = None)"
            name="${elementName}" style="width:100%">
        <?python
            items = sorted(items)
            if 'ALL' in items:
                items.remove('ALL')
                items.insert(0, 'ALL')
        ?>
        <option py:for="value in items" py:content="value" value="${value}" py:attrs="{'selected': (selected == value) and 'selected' or None}" />
    </select>

    <head>
        <title>${formatTitle(operation + ' Permission: %s'% project.getNameForDisplay(maxWordLen = 50))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
            </div>
            
             <div id="innerpage">
                <img class="pagetopleft" src="${cfg.staticPath}/apps/mint/images/innerpage_topleft.png" alt="" />
                <img class="pagetopright" src="${cfg.staticPath}/apps/mint/images/innerpage_topright.png" alt="" />
                
                <div id="right" class="side">
                    ${resourcePane()}
                </div>

                <div id="middle">
                    <h1>${project.getNameForDisplay(maxWordLen = 50)}</h1>
                    <div class="page-title">
                    ${operation} Permission</div>
            
                    <form method="post" action="${(operation == 'Edit') and 'editPerm' or 'addPerm'}">
                        <input py:if="operation=='Edit'" name="oldlabel" value="${label}" type="hidden" />
                        <input py:if="operation=='Edit'" name="oldtrove" value="${trove}" type="hidden" />
                        <table class="add-form">
                            <tr>
                                <td id="header">Role:</td>
                                <td py:if="operation!='Edit'" py:content="makeSelect('role', [x for x in roles if x != cfg.authUser], role)"/>
                                <td py:if="operation=='Edit'"><input name="role" value="${role}" readonly="readonly" type="text" /></td>
                            </tr>
                            <tr>
                                <td id="header">Label:</td>
                                <td py:content="makeSelect('label', labels, label)"/>
                            </tr>
                            <tr>
                                <td id="header">Trove:</td>
                                <td>
                                    <input type="text" name="trove" value="${trove or 'ALL'}" />
                                </td>
                            </tr>
                            <tr>
                                <td id="header" rowspan="3">Options:</td>
                                <td><input type="checkbox" name="writeperm" py:attrs="{'checked': (writeperm) and 'checked' or None}" /> Write access</td>
                            </tr>
                            <tr py:attrs="{'style' :  not cfg.removeTrovesVisible and 'display : none;' or None}">
                                <td><input type="checkbox" name="remove" py:attrs="{'checked': (remove) and 'checked' or None}"/> Remove access</td>
                            </tr>
        
                        </table>
                        <p><input type="submit" value="${operation}"/></p>
                    </form>
                </div><br class="clear" />
                <img class="pagebottomleft" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomleft.png" alt="" />
                <img class="pagebottomright" src="${cfg.staticPath}/apps/mint/images/innerpage_bottomright.png" alt="" />
                <div class="bottom"></div>
            </div>
        </div>
    </body>
</html>