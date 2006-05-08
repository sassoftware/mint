<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
<!--
    Copyright (c) 2005-2006 rPath, Inc.
    All Rights Reserved
-->
    <head py:match="item.tag == '{http://www.w3.org/1999/xhtml}head'"
          py:attrs="item.attrib">
        <link rel="stylesheet" type="text/css" href="${cfg.staticPath}apps/mint/css/mint.css" />
    </head>

    <body py:match="item.tag == '{http://www.w3.org/1999/xhtml}body'"
          py:attrs="item.attrib">

          <h1>${cfg.productName} Help</h1>

          <div py:replace="item[:]" />

          <div id="helpclose">
              <a href="#" onclick="javascript: window.close();">Close</a>
          </div>

    </body>

</html>
