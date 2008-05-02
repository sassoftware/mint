<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#">
<!--
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
-->
  <head>
  </head>
  <body style="padding: 0px; margin: 0px">
    <form enctype="multipart/form-data" method="POST" action="/cgi-bin/fileupload.cgi?id=${id};fieldname=${fieldname}">
        <input name="project" type="hidden" value="${project}"/>
        <input name="uploadfile" type="file"/>
        <input name="fieldname" type="hidden" value="${fieldname}"/>
    </form>
  </body>
</html>
