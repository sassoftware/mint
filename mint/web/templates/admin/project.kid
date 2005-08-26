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
        <a href="#">Project Administration</a>
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
              <form action="administer" method="post">
                <h2>Select a project below to modify</h2>
                <p>
                  <select name="projectId">
                    <option py:for="project in projects" value="${project[0]}" py:content="project[1]"/>
                  </select>
                </p>
                <p>
                  <button name="operation" value="project_delete">Delete Project</button>
                  <button name="operation" value="project_change_members">Change Members</button>
                  <button name="operation" value="project_maillists">Manage Mailing Lists</button>
                  <button name="operation" value="project_edit">Edit</button>
                </p>
              </form>
            </div>
        </td>
    </body>
</html>
