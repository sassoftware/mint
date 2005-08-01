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
        <td id="main" class="spanall">
            <div class="pad">
                <p style="font-size: 150%; font-weight: bold;">Error:</p>
                
                <p style="color: red; margin-left: 1em;">${error}</p>
                <p>
                    Please go back and try again or contact 
                    <a href="mailto:custom@rpath.com">custom@rpath.com</a> or join the IRC channel
                    <b>#conary</b> on the <a href="http://www.freenode.net/">FreeNode</a> IRC network
                    for assistance.
                </p>
            </div>
        </td>
    </body>
</html>
