<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import raa.templates.master ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">

<!--
    Copyright (c) 2006-2007 rPath, Inc.
    All Rights Reserved
-->

<head>
    <title>PostgreSQL Conversion - Index</title>
    <?python
  from raa.templates.callbackdisplaywidget import CallbackDisplayWidget
    ?>
</head>

<body>
    <?python
        schedId = locals().get('schedId', -1)
        statusmsg = locals().get('statusmsg', '')
        status = locals().get('status', '')
    ?>
    <script type="text/javascript">
    var messageBox = new MessageBox();

    function convertNow(link)
    {
        messageBox.doDisplayOverlay();
        messageBox.doDisplay(
            "This process may take up to an hour per project, during which time your rBuilder Appliance will not be available.  Please make sure you have a recent backup before continuing.  Do you really want to convert this appliance?",
            [['Convert Now', function () {
                    initCallbackDisplay();
                    startCallbackDisplay('convert', 'Converting to PostgreSQL...', ['confirm'], [true]);
                    messageBox.doClose();
                    swapDOM($('conv_instructions'), DIV({"id": 'conv_instructions'}));
                }],
                ["Cancel", messageBox, "doClose"]]);
    }

    function finalizeNow(link)
    {
        messageBox.doDisplayOverlay();
        messageBox.doDisplay(
            "Would you like to finalize this repository conversion?  This cannot be undone.",
            [['Finalize Now', function () {
                    /* Do the work here */
                    postRequest('finalize', ['confirm'], [true], createCallbackRedirect(basepath), callbackErrorGeneric);
                    messageBox.doClose();
                    swapDOM($('conv_instructions'), DIV({"id": 'conv_instructions'}));
                }],
                ["Cancel", messageBox, "doClose"]]);
    }

    </script>
    <div class="plugin-page">
    <div class="page-content">

    <!--Status box -->
    ${CallbackDisplayWidget(schedId=schedId, optype="Migrating to PostgreSQL...", statusmsg=statusmsg, status=status)}

    <div py:if="running" id="conv_instructions"/>

    <div py:if="not running and not converted" id="conv_instructions">
        <div class="page-section">
            Convert to PostgreSQL
        </div>
        <div class="page-section-content">
            Clicking the "Convert" button below will convert your rBuilder
            Appliance to use PostgreSQL as its repository backend database.
            PostgreSQL provides better performance, improved concurrency, and
            higher reliability than the previous database backend.  rPath
            recommends that this conversion occur as soon as it may be
            scheduled.  The conversion process will take an hour or less for each
            project hosted on the rBuilder (internal, or external with mirrors). 
            This process is reversible if an error occurs, but rPath suggests
            that backups be taken before executing the conversion.
            <p></p>
            After clicking the Convert button below, a progress indicator
            will appear.  An OK button will appear after the conversion is
            complete.  Check your appliance for completeness and
            functionality, and then click the "Finalize Conversion"
            button to remove the old databases to free up space.

            <div class="button-line">
            <a class="rnd_button internal float-left" id="convertbutton" onclick="javascript:convertNow();">Convert</a>
            </div>
        </div>
    </div>

    <div py:if="not running and converted and not finalized" id="conv_instructions">
        <div class="page-section">
            PostgreSQL Conversion Completed
        </div>
        <div class="page-section-content">
            Your system has been successfully converted to use PostgreSQL as
            the database backend.  Click "Finalize Conversion" below to make this
            change permanent, and remove the old databases.  Once you have
            finalized, you may not revert this change.
            <p></p>
            If you need to revert this change, do not finalize at this time.
            Instead please contact rPath Support for instructions.

            <div class="button-line">
            <a class="rnd_button internal float-left" id="finalizebutton" onclick="javascript:finalizeNow();">Finalize</a>
            </div>
        </div>
    </div>

    </div>
    </div>
</body>
</html>
