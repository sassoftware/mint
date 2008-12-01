<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
import raa 
import raa.templates.master 
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">

<!--
Copyright (c) 2006-2008 rPath, Inc.
    All Rights Reserved
-->

<head>
    <title>rBuilder Setup</title>
    <?python
        from raa.web import makeUrl
        import socket
        host = socket.gethostname()
        url = "http://" + host + "/setup/"
    ?>
    <script type="text/javascript">
        function redirect(url)
        {
            window.open(url, 'config');
        }
    </script>
</head>

<body>
<div class="plugin-page" id="plugin-page">
     <div py:if="raaInWizard" class="page-section">rBuilder Setup</div>
     <div class="page-section-content-bottom">

    <br/>
    The system level configuration of rBuilder is complete.  Click 'Continue' to finish the configuration process.
        
    <br/><br/>
    <form action="javascript:void(0);" method="POST" id="page_form" name="page_form"
	    onsubmit="javascript:postFormWizardRedirectOnSuccess(this,'doSetup');redirect('${url}')">
	    <a class="rnd_button float-right" id="OK" href="javascript:button_submit(document.page_form)">Continue</a>
    </form>
    </div>
</div>
</body>
</html>
