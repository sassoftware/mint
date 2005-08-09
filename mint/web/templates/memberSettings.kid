<?xml version='1.0' encoding='UTF-8'?>
<?python
from mint import userlevels
?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <head>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/basic.css"/>
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/contentTypes.css"/>
    </head>
    <body style="background-color:transparent; padding:0px;" onload="window.parent.show_popup('memberEditBox');">
        <div class="side">
            <div class="palette">
                <h3>Edit Member</h3>
                <form method="post" action="editMember">
                    <p>
                        <label>Membership Status:</label><br />
                        <select name="level">

                            <option py:for="level, levelName in userlevels.names.items()"
                                    py:content="levelName"
                                    value="${level}"
                                    py:attrs="{'selected': level == otherUserLevel and 'selected' or None}" />
                        </select>
                    </p>
                    <button type="submit" onclick="window.parent.hide_popup('memberEditBox', true);">Submit</button>
                    <input type="hidden" name="userId" value="${userId}"/>
                    <button type="button" onclick="window.parent.hide_popup('memberEditBox', false);">Cancel</button>
                </form>
            </div>
        </div>
    </body>
</html>
