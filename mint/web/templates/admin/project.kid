<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'administer.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        ${adminbreadcrumb()}
        <a href="administer?operation=project">Project Administration</a>
    </div>

    <head>
        <title>${formatTitle('Administer Projects')}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${browseMenu()}
                ${searchMenu()}
            </div>
        </td>
        <td id="main" class="spanall">
            <div class="pad">
              <p py:if="kwargs.get('extraMsg', None)" class="message" py:content="kwargs['extraMsg']"/>
              <form action="administer" method="post">
                <h2>Select a project below to modify</h2>
                <p>
                  <select name="projectId">
                    <option py:for="project in projects" value="${project[0]}" py:attrs="{'class': project[1] and 'disabledOption' or None, 'class': project[2] and 'hiddenOption' or None}" py:content="project[3]"/>
                  </select>
                </p>
                <p>
                  <button name="operation" value="project_hide">Hide Project</button>
                  <button name="operation" value="project_unhide">Unhide Project</button>
                  <button name="operation" value="project_disable">Disable Project</button>
                  <button name="operation" value="project_enable">Enable Project</button>
                  <button name="operation" value="project_change_members">Change Members</button>
                  <button name="operation" value="project_maillists">Manage Mailing Lists</button>
                  <button name="operation" value="project_edit">Edit</button>
                </p>
              </form>
            </div>
        </td>
    </body>
</html>
