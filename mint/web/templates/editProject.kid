<?xml version='1.0' encoding='UTF-8'?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'layout.kid'">
<!--
    Copyright (c) 2005-2007 rPath, Inc.
    All Rights Reserved
-->
    <head>
        <title>${formatTitle('Project Settings: %s'%project.getNameForDisplay())}</title>
    </head>
    <body>
        <div id="layout">
            <div id="right" class="side">
                ${resourcePane()}
                ${builderPane()}
            </div>

            <div id="spanleft">
                <h2>Edit Project Properties</h2>
                <form method="post" action="${basePath}processEditProject">
                    <table border="0" cellspacing="0" cellpadding="0" class="mainformhorizontal">
                        <tr>
                            <th>Project Title</th>
                            <td>
                                <input type="text" name="name" value="${kwargs['name']}" />
                                <p class="help">The title is a longer, more descriptive name for your project, such as "<strong>My Custom Linux</strong>."
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th>Default Branch Name</th>
                            <td>
                                <input type="text" name="branch" value="${kwargs['branch']}" />
                                <p class="help">The default Conary branch name for your project.
                                    A branch name consists of: &lt;namespace&gt;:&lt;tag&gt;. Refer to
                                    <a href="http://wiki.rpath.com/wiki/Conary:Concepts">Conary Concepts</a>
                                        for more information about branch names.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <th>Is This a Software Appliance?</th>
                            <td>
                                <select style="width: auto;" name="appliance">
                                    <option py:attrs="{'selected': 'selected' and (kwargs['appliance'] == 'unknown') or None}" value="unknown">---</option>
                                    <option py:attrs="{'selected': 'selected' and (kwargs['appliance'] == 'yes') or None}" value="yes">Yes</option>
                                    <option py:attrs="{'selected': 'selected' and (kwargs['appliance'] == 'no') or None}" value="no">No</option>
                                </select>
                                <p class="help">Please select "yes" if this project's main purpose is to produce a software appliance.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>Project Description</th>
                            <td>
                                <textarea name="desc" cols="70" rows="12">${kwargs['desc']}</textarea>
                                <p class="help">It may be useful to put alternate branch labels, project goals,
                                    mechanisms for joining a project, or other relevant information here.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>Project Home Page</th>
                            <td>
                                <input type="text" name="projecturl" value="${kwargs['projecturl']}" />
                                <p class="help">A link to an external site providing more information, forums, documentation, etc.</p>
                            </td>
                        </tr>
                        <tr>
                            <th>Repository Commits Email</th>
                            <td>
                                <input type="text" name="commitEmail" value="${kwargs['commitEmail']}" />
                                <p class="help">An email address to which Conary repository commit messages are sent to.</p>
                            </td>
                        </tr>

                    </table>

                    <button class="img" type="submit"><img src="${cfg.staticPath}apps/mint/images/submit_button.png" alt="Submit" /></button>
                </form>
            </div>
        </div>
    </body>
</html>
