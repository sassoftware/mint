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
        <td id="main" class="spanleft" >
            <div class="pad">
                <h2>Create an Project</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="createProject">

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Project Title:</em></th>
                            <td>
                                <input type="text" name="title" />
                                <p class="help">please limit to 16 characters</p>
                            </td>
                        </tr>

                        <tr>
                            <th><em class="required">Repository Hostname:</em></th>
                            <td>
                                <input type="text" name="hostname" /> .rpath.org
                                <p class="help">Please choose a hostname for your repository. It must start with a letter and contain only letters, numbers, and hyphens.</p>
                            </td>
                        </tr>
                        <tr>

                            <th>Project Description:</th>
                            <td>
                                <textarea rows="6" name="blurb"></textarea>
                            </td>
                        </tr>
                    </table>
                    <p><button type="submit">Create</button></p>
                </form>
            </div>
        </td>
        <td id="right" class="plain">
            <div class="pad">
            </div>
        </td>
    </body>
</html>
