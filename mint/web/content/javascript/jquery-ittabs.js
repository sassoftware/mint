/**
 * Interface Elements for jQuery
 * TTabs
 * 
 * http://interface.eyecon.ro
 * 
 * Copyright (c) 2006 Stefan Petre
 * Dual licensed under the MIT (MIT-LICENSE.txt) 
 * and GPL (GPL-LICENSE.txt) licenses.
 *   
 * Modified by Scott Parkerson to use 4 spaces rather than tab characters.
 *
 */

jQuery.iTTabs =
{
        isIE : function(el)
        {
                return (el.selectionStart == undefined);
        },
        getCaretPosition : function(el)
        {
            if (jQuery.iTTabs.isIE(el)) /* IE 6+ */
            {
                    var sel = document.selection.createRange();
                    var tSel = el.createTextRange();
                    tSel.moveToBookmark(sel.getBookmark());
                    return Math.abs(tSel.move('character', -el.value.length));
            }
            else if (el.selectionStart) /* Webkit, Firefox, Opera */
            {
                    return el.selectionStart;
            }
            else /* don't know what to do, punt */
            {
                    return 0;
            }
        },
        getSpacesNeeded : function(el, start)
        {
                if (jQuery.iTTabs.isIE(el) && el.wrap)
                {
                        /* Need to normalize IE's line endings */
                        var textboxContents = el.value.replace(/\r\n?/g, '\n');
                }
                else
                {
                        var textboxContents = el.value;
                }
                var lineBeginningPos = textboxContents.substring(0,start).lastIndexOf('\n') + 1;
                //alert(lineBeginningPos);
                return 4 - ((start - lineBeginningPos) % 4);
        },
        makeFakeTab : function(spacesNeeded)
        {
                var stringToInsert = '';
                for (var i = 0; i < spacesNeeded; i++)
                {
                        stringToInsert += ' ';
                }
                return stringToInsert;
        },
        doTab : function(e)
        {
                pressedKey = e.charCode || e.keyCode || -1;
                if (pressedKey == 9) {
                        if (jQuery.iTTabs.isIE(this))
                        {
                                window.event.cancelBubble = true;
                                window.event.returnValue = false;
                        }
                        else
                        {
                                e.preventDefault();
                                e.stopPropagation();
                        }
                        var start = jQuery.iTTabs.getCaretPosition(this);
                        //alert(start);
                        var spacesNeeded = jQuery.iTTabs.getSpacesNeeded(this, start);
                        if (jQuery.iTTabs.isIE(this))
                        {
                                document.selection.createRange().text = jQuery.iTTabs.makeFakeTab(spacesNeeded);
                                this.onblur = function() { this.focus(); this.onblur = null; };
                        }
                        else if (this.setSelectionRange) /* Firefox, Safari, Opera */
                        {
                                var end = this.selectionEnd + spacesNeeded;
                                this.value = this.value.substring(0, start) +
                                    jQuery.iTTabs.makeFakeTab(spacesNeeded) + this.value.substr(start);
                                this.setSelectionRange(end, end);
                                this.focus();
                        }
                        return false;
                }
        },
        destroy : function()
        {
                return this.each(
                        function()
                        {
                                if (this.hasTabsEnabled && this.hasTabsEnabled == true) {
                                        jQuery(this).unbind('keydown', jQuery.iTTabs.doTab);
                                        this.hasTabsEnabled = false;
                                }
                        }
                );
        },
        build : function()
        {
                return this.each(
                        function()
                        {
                                if (this.tagName == 'TEXTAREA' && (!this.hasTabsEnabled || this.hasTabsEnabled == false)) {
                                        jQuery(this).bind('keydown', jQuery.iTTabs.doTab);
                                        this.hasTabsEnabled = true;
                                }
                        }
                );
        }
};

jQuery.fn.extend (
        {
                /**
                 * Enable tabs in textareas
                 * 
                 * @name EnableTabs
                 * @description Enable tabs in textareas
                 *
                 * @type jQuery
                 * @cat Plugins/Interface
                 * @author Stefan Petre
                 */
                EnableTabs : jQuery.iTTabs.build,
                /**
                 * Disable tabs in textareas
                 * 
                 * @name DisableTabs
                 * @description Disable tabs in textareas
                 *
                 * @type jQuery
                 * @cat Plugins/Interface
                 * @author Stefan Petre
                 */
                DisableTabs : jQuery.iTTabs.destroy
        }
);
