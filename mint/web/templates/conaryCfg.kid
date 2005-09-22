<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Conary Configuration</a>
    </div>

    <head>
        <title>${formatTitle('Conary Settings: %s'%project.getName())}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>

        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />Conary Settings</h2>
                <p>To add this project in your Conary configuration, add <tt><strong>${project.getLabel()}</strong></tt> to the <tt><strong>installLabelPath</strong></tt> line in the <tt><strong>/etc/conaryrc</strong></tt> (or your <tt><strong>~/.conaryrc</strong></tt>) file.</p>
            </div>
        </td>
        ${projectsPane()}        
    </body>
</html>
