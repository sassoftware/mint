<?xml version='1.0' encoding='UTF-8'?>
<html xmlns:html="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
      py:extends="'library.kid', 'layout.kid', 'project.kid'">
<!--
    Copyright 2005 rPath, Inc.
    All Rights Reserved
-->
    <div py:def="breadcrumb()" py:strip="True">
        <a href="$basePath">${project.getName()}</a>
        <a href="#">Conary Settings</a>
    </div>

    <head>
        <title>${formatTitle('Conary Settings: %s'%project.getName())}</title>
    </head>
    <body>
        <td id="left" class="side">
            <div class="pad">
                ${projectResourcesMenu()}
            </div>

        </td>
        <td id="main">
            <div class="pad">
                <h2>${project.getName()}<br />Conary Settings</h2>

                <p>You have two options available to you if you want to
                install software from this project:</p>

                <ul>

                    <li>You can perform an installation by specifying this
                    project's label as part of the <tt>conary</tt>
                    command.</li>

                    <li>You can configure Conary to automatically search
                    this project's label so that subsequent <tt>conary</tt>
                    commands need not explicitly specify it.</li>

                </ul>

                    <h3>Which option should I choose?</h3>

                        <p>It really depends on what your long-term
                        expectations are with respect to this project.</p>

                        <p>If this project has only one trove that
                        interests you, specify the label as part of the
                        <tt>conary</tt> command.  Note that this does
                        <em>not</em> prevent Conary from accessing this
                        project's repository to find (and install) updates
                        to the software you install &#8212; Conary takes
                        care of that for you.</p>

                        <p>On the other hand, if this project has lots of
                        interesting software and you expect that you'll be
                        coming back from time to time to see what
                        newly-available software there is, you should
                        configure Conary to automatically search this
                        project's label.</p>

                    <h3>How do I do it?</h3>

                        <h4>Specifying This Project's Label as Part of the Conary command</h4>

                            <p>Use the following command format to specify
                            this project's label when issuing a <tt>conary
                            update</tt> command:</p>

                            <tt><strong>conary update &lt;trove&gt;=${project.getLabel()}</strong></tt>

                            <p>(Where <tt>&lt;trove&gt;</tt> represents the
                            name of the trove to be installed.)</p>

                        <h4>Configuring Conary to Automatically Search this Project's Label</h4>

                            <p>To configure Conary to automatically search
                            this project's label you must use a text editor
                            to add the label to Conary's main configuration
                            file, <tt>/etc/conaryrc</tt>.</p>

                            <p>NOTE: You must be the root user (either by
                            logging in as root, or by using the <tt>su</tt>
                            command) to edit this file.</p>

                            <p>The option you must modify is
                            <tt>installLabelPath</tt>.  This option
                            contains the list of labels that Conary
                            searches when performing the initial
                            installation of a trove.  The order of labels
                            in the list determines the order in which they
                            will be searched.</p>

                            <p>You can display the current
                            <tt>installLabelPath</tt> setting by using the
                            following command:</p>

                            <tt><strong>conary config | grep installLabelPath</strong></tt>

                            <p>If this project's label is already be
                            included in your system's
                            <tt>installLabelPath</tt>, you don't need to
                            make any changes at all &#8212; just install
                            the desired trove using the <tt>conary
                            update</tt> command shown at the end of this
                            page.</p>

                            <p>However, if this project's label is not
                            currently included in your system's
                            <tt>installLabelPath</tt>, you must add it.</p>

                            <p>Using the text editor of your choice, open
                            <tt>/etc/conaryrc</tt>, and find the
                            <tt>installLabelPath</tt> line.  At this point,
                            you must decide where in the list to place this
                            project's label.</p>

                            <p>In most cases, you can just add the
                            project's label to the end of the list (Note:
                            Even though it can be quite long, the list
                            <em>must</em> remain on one line):</p>

                            <tt><strong>installLabelPath &lt;label1&gt; ... &lt;labelN&gt; ${project.getLabel()}</strong></tt>

                            <p>This approach would not work if one or more
                            labels in the list had troves with the same
                            names as those in the project's label.  In that
                            case, this project's label should be inserted
                            before the labels with the same-named
                            troves:</p>

                            <tt><strong>installLabelPath ${project.getLabel()} &lt;label1&gt; ... &lt;labelN&gt;</strong></tt>

                            <p>Once you've added the project's label, the
                            Conary command you'll use to install troves
                            from the project's repository takes the
                            form:</p>

                            <tt><strong>conary update &lt;trove&gt;</strong></tt>

                            <p>(Where <tt>&lt;trove&gt;</tt> represents the
                            name of the trove to be installed.)</p>

            </div>
        </td>
        ${projectsPane()}        
    </body>
</html>
