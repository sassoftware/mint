<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'../layout.kid'">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Administer Projects')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
              <p py:if="kwargs.get('extraMsg', None)" class="message" py:content="kwargs['extraMsg']"/>
              <form action="${cfg.basePath}admin/processProjectAction" method="post">
	        <a href ="${cfg.basePath}admin">Return to Administrator Page</a>
                <h2>Select a project below to modify</h2>
                <p>Key
                    <ul>
                        <li>Normal Project</li>
                        <li><span style="color: #999;">Hidden Project</span></li>
                        <li><span style="text-decoration: line-through;">Disabled Project</span></li>
                        <li><span style="color: #999; text-decoration: line-through;">Hidden/Disabled Project</span></li>
                    </ul>
                  <select name="projectId">
                    <div py:strip="True" py:for="project in projects">
                      <?python
                          classStr = ""
                          if project[1]:
                              classStr += "text-decoration: line-through;"
                          if project[2]:
                              classStr += "color: #999;"
                      ?>
                      <option value="${project[0]}" py:attrs="{'style': classStr and classStr or None}" py:content="project[3]"/>
                    </div>
                  </select>
                </p>
                <p>
                   <button name="operation" value="project_toggle_hide">Hide/Unhide Project</button>
                   <button name="operation" value="project_toggle_disable">Enable/Disable Project</button>
                </p>
              </form>
            </div>
        </td>
    </body>
</html>
