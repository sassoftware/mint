<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Email Confirmation Required')}</title>
    </head>
    <body>
        <td id="main" class="spanall">
            <div class="pad">
		<p class="error">Email Confirmation Required:</p>
                <p class="errormessage">You have been redirected to this page because you have not yet confirmed your email address</p>
		<p>You will be required to do so before continuing.</p>
		<p>If you would like to use a different email address, please enter it below</p>
		<form method="post" action="editUserSettings">
			<input type="text" name="email" value="${auth.email}"/>
			<p/><button type="submit">Submit</button>
		</form>
            </div>
        </td>
    </body>
</html>
