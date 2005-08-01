<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb" class="pad">
        You are here:
        <a href="#">rpath</a>
        <a href="/">${project.getName()}</a>
        <a href="#">Edit Description</a>
    </div>


    <head/>
    <body>
        <td id="main" class="spanleft">
            <div class="pad">
                <h2>Edit Project Description</h2>

                <form method="post" action="editProjectDesc">
                    <textarea name="desc" cols="70" rows="12">${project.getDesc()}</textarea>

                    <p style="margin-top: 1em;"><button type="submit">Submit</button></p>
                </form>
            </div>
        </td>
        ${projectsPane()}
    </body>
</html>
