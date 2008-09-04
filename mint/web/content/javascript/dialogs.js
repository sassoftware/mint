/*
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
*/

/*
 * Displays a modal dialog with an overlay and Yes/No buttons.  You must supply
 * a func to be run for Yes and No.  This is not async, so the dialog will not
 * close until the supplied func returns.
 */
function modalYesNo(yesFunc, noFunc) {
    jQuery("#modalYesNo").dialog({ 
        modal: true,
        draggable: false,
        width: 450,
        height: 200,
        overlay: { 
            opacity: 0.5, 
            background: "black" 
        },
        buttons: { 
	        "Yes": function() {
	        	yesFunc();
	        	jQuery(this).dialog("close");
	        },
	        "No": function() { 
	            noFunc();
                jQuery(this).dialog("close");
	        }
        }
    }).show();
}

function modalEditVersionWarning(yesFunc, noFunc) {
    jQuery("#modalEditVersionWarning").dialog({
        modal: true,
        draggable: false,
        width: 450,
        height: 250,
        overlay: { 
            opacity: 0.5, 
            background: "black" 
        },
        buttons: {
            "Add Image Later": function() {
                yesFunc();
                jQuery(this).dialog("close");
            },
            "Add Image Now": function() { 
                noFunc();
                jQuery(this).dialog("close");
            }
        }
    }).show();
}
