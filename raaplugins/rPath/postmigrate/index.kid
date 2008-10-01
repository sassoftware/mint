<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">
    <!--
         Copyright (c) 2007 rPath, Inc.
         All rights reserved
    -->
    <head>
        <title py:if="not complete">Prepare rBuilder for Migration</title>
        <title py:if="complete">rBuilder Migration was Successful</title>
        <?python
            from raa.templates.callbackdisplaywidget import CallbackDisplayWidget
        ?>
    </head>

    <body>
        <div class="plugin-page">
        <div py:strip="True" py:if="not complete">
            <script type="text/javascript">
                function doRestore(link, filename)
                {
                    removeElement(link);
                    removeElement(getElement('guide_text'));

                    initCallbackDisplay();
                    startCallbackDisplay('doRestore', 'Performing restoration...', ['filename'], [filename]);
                }
            </script>
            <div class="page-section">
            rBuilder Migration
            </div>
            <div class="page-section-content">
                <div py:strip="True" py:if="prompt">
                    <div class="page-subsection-instr">
                        Is this system being upgraded from a previous version?
                    </div>
                    <form action="index" method="GET" name="index_form">
                        <input type="hidden" name="restore" value="True"/>
                        <a class="rnd_button float-left" id="yes_button" href="javascript:button_submit(document.index_form)">Yes</a>
                    </form>
                    <form name="no_form" action="javascript:void(0);" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'skipPlugin');">
                        <a class="rnd_button float-left" id="no_button" href="javascript:button_submit(document.no_form)">No</a>
                    </form>
                </div>
                <div py:strip="True" py:if="not prompt">
                    <div py:strip="True" py:if="not diskPresent">
                    <div class="page-subsection-instr">
                        In order to proceed, please attach the disk containing your stored data now.
                    </div>
                    <form name="scan_form" action="index" method="GET">
                        <input type="hidden" name="restore" value="True"/>
                        <a class="rnd_button float-left" id="scan" href="javascript:button_submit(document.scan_form)">Scan System</a>
                    </form>
                    </div>
                    <div py:strip="True" py:if="diskPresent">
                        <div py:strip="True" py:if="not backups">
                        <div class="page-subsection-instr">
                            Backup device was found, but no valid backups were present.
                        </div>
                        </div>
                        <div py:strip="True" py:if="backups">
                        <div class="page-subsection-instr">
                                    You are now ready to proceed. Click "Restore Now" to restore your data and complete this migration.
                        </div>
                        ${CallbackDisplayWidget()}
                        <table>
                            <tr py:for="id, filename in enumerate(backups)" py:attrs="{'class': id % 2 and 'odd' or 'even'}">
                                <td>${filename}</td>
                                <td>
                                    <a class="rnd_button float-left" id="restore_button" href="javascript:doRestore(this, '${filename}');">Resotre Now</a>
                                </td>
                            </tr>
                        </table>
                        </div>
                    </div>
                    <form name="skip_form" action="javascript:void(0);" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'skipPlugin');">
                        <a class="rnd_button float-left" id="skip" href="javascript:button_submit(document.skip_form)">Skip</a>
                    </form>
                </div>
            </div>
        </div>

        <div py:strip="True" py:if="complete">
            <div class="page-section">
            Congratulations.
            </div>
            <div class="page-section-content">
            This rBuilder appliance has been successfully migrated.
            <form name="skip_plugin_form" action="javascript:void(0);" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'skipPlugin');">
                <a class="rnd_button float-left" id="skip_plugin_button" href="javascript:button_submit(document.skip_plugin_form)">Done</a>
            </form>
            </div>
        </div>

        </div>
    </body>
</html>
