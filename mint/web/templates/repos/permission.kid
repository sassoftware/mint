<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<?python
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
?>
    <!-- creates a selection dropdown based on a list -->
    <select py:def="makeSelect(elementName, items, selected = None)"
            name="${elementName}">
        <?python
            items = sorted(items)
            if 'ALL' in items:
                items.remove('ALL')
                items.insert(0, 'ALL')
        ?>
        <option py:for="value in items"
                py:content="value" value="${value}" py:attrs="{'selected': (selected == value) and 'selected' or None}" />
    </select>

    <head>
        <title>${formatTitle('Repository Browser: %s'% project.getNameForDisplay(maxWordLen = 50))}</title>
    </head>
    <body>
        <div id="layout">
            <div id="left" class="side">
                ${projectResourcesMenu()}
                ${releasesMenu(project.getReleases(), isOwner)}
                ${commitsMenu(project.getCommits())}
            </div>
            <div id="spanright">
            <h2>${operation} Permission</h2>
            <form method="post" action="${(operation == 'Edit') and 'editPerm' or 'addPerm'}">
                <input py:if="operation=='Edit'" name="oldlabel" value="${label}" type="hidden" />
                <input py:if="operation=='Edit'" name="oldtrove" value="${trove}" type="hidden" />
                <table class="add-form">
                    <tr>
                        <td id="header">Group:</td>
                        <td py:if="operation!='Edit'" py:content="makeSelect('group', groups, group)"/>
                        <td py:if="operation=='Edit'"><input name="group" value="${group}" readonly="readonly" type="text" /></td>
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
                        <td id="header" rowspan="2">Options:</td>
                        <td><input type="checkbox" name="writeperm" py:attrs="{'checked': (writeperm) and 'checked' or None}" /> Write access</td>
                    </tr>
                    <tr style="display: none;">
                        <td><input type="checkbox" name="capped" py:attrs="{'checked': (capped) and 'checked' or None}" /> Capped</td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" name="admin" py:attrs="{'checked': (admin) and 'checked' or None}" /> Admin access</td>
                    </tr>

                </table>
                <p><input type="submit" value="${operation}"/></p>
            </form>
            </div>
        </div>
    </body>
</html>
