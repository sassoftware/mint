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
            from raa.widgets.callbackdisplay import CallbackDisplayWidget
        ?>
    </head>

    <body id="middle">
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
            <h2>rBuilder Migration</h2>
            <div py:strip="True" py:if="prompt">
                <h4>
                    <p>
                        Is this system being upgraded from a previous version?
                    </p>
                    <form action="index" method="GET">
                        <input type="hidden" name="restore" value="True"/>
                        <input class="button" type="submit" value="Yes"/>
                    </form>
                    <form action="javascript:void(0);" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'skipPlugin');">
                        <input class="button" type="submit" value="No"/>
                    </form>

                </h4>
            </div>
            <div py:strip="True" py:if="not prompt">
                <div py:strip="True" py:if="not diskPresent">
                    <h4>
                        <p>
                            In order to proceed, please attach the disk containing your stored data now.
                        </p>
                        <form action="index" method="GET">
                            <input type="hidden" name="restore" value="True"/>
                            <input class="button" type="submit" value="Scan System"/>
                        </form>
                    </h4>
                </div>
                <div py:strip="True" py:if="diskPresent">
                    <div py:strip="True" py:if="not backups">
                        <h4>
                            <p>
                                Backup device was found, but no valid backups were present.
                            </p>
                        </h4>
                    </div>
                    <div py:strip="True" py:if="backups">
                        <h4>
                            <p id="guide_text">
                                You are now ready to proceed. Click "Restore Now" to restore your data and complete this migration.
                            </p>
                        </h4>
                        ${CallbackDisplayWidget().display()}
                        <table>
                            <tr py:for="id, filename in enumerate(backups)" py:attrs="{'class': id % 2 and 'odd' or 'even'}">
                                <td>${filename}</td>
                                <td><input class="button" type="submit" value="Restore Now" onclick="javascript:doRestore(this, '${filename}');" /></td>
                            </tr>
                        </table>
                    </div>
                </div>
                <form action="javascript:void(0);" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'skipPlugin');">
                    <input class="button" type="submit" value="Skip"/>
                </form>
            </div>
        </div>
        <div py:strip="True" py:if="complete">
            <h2>Congratulations.</h2>
            <h4>
                <p>This rBuilder appliance has been successfully migrated.</p>
            </h4>
            <form action="javascript:void(0);" method="POST" onsubmit="javascript:postFormWizardRedirectOnSuccess(this, 'skipPlugin');">
                <input class="button" type="submit" value="Done"/>
            </form>
        </div>
    </body>
</html>
