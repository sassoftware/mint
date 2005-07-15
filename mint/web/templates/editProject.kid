<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head/>
    <body>
        <td id="content">
            <h2>Edit Project Description</h2>

            <form method="post" action="editProjectDesc">
                <textarea name="desc" cols="70" rows="12">${project.getDesc()}</textarea>

                <p><input type="submit" value="Submit" /></p>
            </form>
        </td>
    </body>
</html>
