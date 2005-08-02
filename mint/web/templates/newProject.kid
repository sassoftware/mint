<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid'">
<!--
    Copyright 2005 rpath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="#">Create a Project</a>
    </div>

    <head/>
    <body>
        <td id="main" class="spanleft" >
            <div class="pad">
                <h2>Create a Project</h2>
                <p>Fields labeled with a <em class="required">red arrow</em> are required.</p>
                <form method="post" action="createProject">

                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th><em class="required">Project Name:</em></th>
                            <td>
                                <input type="text" name="hostname" /> .rpath.org
                                <p class="help">Please choose a name for your project. This will be used as the hostname for your project site and repository (http://myproj.rpath.org/) and the prefix for all of the project mailing lists. It must start with a letter and contain only letters and numbers, and be less than or equal to 16 characters long.</p>
                            </td>
                        </tr>

                        <tr>
                            <th><em class="required">Project Title:</em></th>
                            <td>
                                <input type="text" name="title" />
                                <p class="help">The title is a longer, more descriptive name for your project. Eg., <strong>My Custom Linux</strong></p>
                            </td>
                        </tr>

                        <tr>

                            <th>Project Description:</th>
                            <td>
                                <textarea rows="6" name="blurb"></textarea>
                            </td>
                        </tr>
                        <?python
                            from mint import mailinglists
                        ?>
                        <tr>
                            <th>Additional Mailing Lists:</th>
                            <td>
                                <div class="pad">
                                    <span py:for="listid in mailinglists.optionallists" style="margin-right: 1em;">
                                        <input class="check" type="checkbox"
                                               name="optlists" value="${listid}"/>
                                            ${mailinglists.listnames[listid]%'projectname'}
                                    </span>
                                </div>
                                <p class="help">Two mailing lists will be created automatically, one
                                    matching your project name, and projectname-commits.  Select additional
                                    lists to create.  You may create new lists at any time from your
                                    projects administration page.
                                </p>
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
