<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
import raa 
import raa.templates.master 
?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="raa.templates.master">

<!--
Copyright (c) 2006-2009 rPath, Inc.
    All Rights Reserved
-->

<head>
    <title>Next Steps</title>
    <?python
        from raa.web import makeUrl
        import socket
        host = socket.gethostname()
        url = "http://" + host + "/cloudCatalog#/event/navigateToNode/groupName=CLOUDS_GROUP"
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
     <div py:if="raaInWizard" class="page-section">Next Steps</div>
     <div class="page-section-content-bottom">

    <br/>
    Your rBuilder is now configured.  The list below contains other tasks you may wish to complete at this time:
    <ul>
        <li><strong>Configure Targets</strong></li>
        To configure targets such as EC2, VMware, and Citrix Xen, log in to your rBuilder and click on the "rPath Management Console" link.
        <br/><br/>
        <li><strong>Create a New Product</strong></li>
        To create a new product, log in to your rBuilder and click on the "Create a new product" link.
    </ul>
        
    <br/><br/>
    <form action="javascript:void(0);" method="POST" id="page_form" name="page_form"
	    onsubmit="javascript:postFormWizardRedirectOnSuccess(this,'doSetup');">
	    <a class="rnd_button float-right" id="OK" href="javascript:button_submit(document.page_form)">Finish</a>
    </form>
    </div>
</div>
</body>
</html>
