/*
    Copyright (c) 2008 rPath, Inc.
    All Rights Reserved
*/
var currentBdefSerial = 0;
var currentUsourceSerial = 0;

jQuery(document).ready(function () {

    currentBdefSerial = jQuery(".pdbuilddef-deleter").length;
    currentUsourceSerial = jQuery(".pdusource-deleter").length;

    jQuery('select.pdbuilddef-picker-buildType').change(function() {
        var builddefElement = jQuery(this).parents('tr').get(0);
        var builddefmoreElement= jQuery(builddefElement).next().get(0);
        var archSelectorElement = jQuery(builddefElement).children('td').get(2);
        var buildtype = this.value;
        var buildtypeclass = '.it-'+buildtype;
        var archtypeclass = '.arch-'+buildtype;

        jQuery(builddefmoreElement).find('div.it-'+buildtype).each(function () {
            jQuery(this).show();
            jQuery(this).find(':input').removeAttr('disabled');
        });
        jQuery(builddefmoreElement).find('div:not(.it-'+buildtype+')').each(function () {
            if (jQuery(this).is(':not(.clearleft)')) {
                jQuery(this).hide();
            }
            jQuery(this).find(':input').attr('disabled', 'disabled');
        });
        
        // handle arch selectors
        jQuery(archSelectorElement).find('select:not(.arch-'+buildtype+')').each(function () {
            if (jQuery(this).is(':not(.clearleft)')) {
                jQuery(this).hide();
                jQuery(this).attr('disabled', 'disabled');
            }
        });
        jQuery(archSelectorElement).find('select.arch-'+buildtype).each(function () {
            jQuery(this).show();
            jQuery(this).removeAttr('disabled');
        });
    });

    jQuery('.pdbuilddef-adder,.pdbuilddef-expander,.pdbuilddef-deleter,.pdusource-adder,.pdusource-deleter').hover(function () {
            var imgbutton = jQuery(this).find('img').get(0);
            imgbutton.src = imgbutton.src.replace('.gif', '_h.gif');
        }, function() {
            var imgbutton = jQuery(this).find('img').get(0);
            imgbutton.src = imgbutton.src.replace('_h.gif', '.gif');
    });

    jQuery('.pdbuilddef-expander').click(function () {
            var imgbutton = jQuery(this).find('img').get(0);
            var builddefId = "#" + jQuery(this).parents().get(1).id;
            var builddefmoreId = builddefId + "-more";
            if (jQuery(builddefId).attr('class') == 'pdbuilddef-expanded') {
                jQuery(builddefmoreId).hide();
                jQuery(builddefId).removeAttr('class');
                jQuery(builddefmoreId).removeAttr('class');
            } else {
                jQuery(builddefmoreId).show();
                jQuery(builddefId).attr('class', 'pdbuilddef-expanded');
                jQuery(builddefmoreId).attr('class', 'pdbuilddef-more');
            }
    });

    jQuery('.pdbuilddef-deleter').click(function () {
            var builddefId = "#" + jQuery(this).parents().get(1).id;
            var builddefmoreId = builddefId + '-more';
            jQuery(builddefId).remove();
            jQuery(builddefmoreId).remove();
            
            // show the no entries found if last one removed
            var tbody = jQuery('#pdbuilddefs > tbody');
            if (tbody.find('tr').length <= 1) {
                jQuery('#pdbuilddef-empty').show();
            }
    });

    jQuery('.pdbuilddef-adder').click(function () {
        var templateDomBits = jQuery('#pdbuilddef-bt-all > tbody').clone(true);
        templateDomBits.find(':disabled').removeAttr('disabled');
        templateDomBits.find('label').each(function () {
            this.htmlFor = this.htmlFor.replace('bt', String(currentBdefSerial));
        });
        templateDomBits.find('input,select').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentBdefSerial)); }
            if (this.name) { this.name = this.name.replace('bt', String(currentBdefSerial)); }
            if (this.value == 'NEWBUILD') { this.value = "New Build " + currentBdefSerial; }
        });
        templateDomBits.find('tr').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentBdefSerial)); }
        });
        templateDomBits.find('select').change();
        templateDomBits.children().appendTo('#pdbuilddefs > tbody');
        
        // hide the no entries found message
        jQuery('#pdbuilddef-empty').hide();
        currentBdefSerial++;
    });

    jQuery('.pdusource-deleter').click(function () {
            var usourceId = "#" + jQuery(this).parents().get(1).id;
            jQuery(usourceId).remove();
            // show the no entries found if last one removed
            var tbody = jQuery('#pdusource > tbody');
            if (tbody.find('tr').length <= 1) {
                jQuery('#pdusource-empty').show();
            }
    });
    
    jQuery('.pdusource-adder').click(function () {
        currentUsourceSerial++;
        var templateDomBits = jQuery('#pdusource-bt-all > tbody').clone(true);
        templateDomBits.find(':disabled').removeAttr('disabled');
        templateDomBits.find('label').each(function () {
            this.htmlFor = this.htmlFor.replace('bt', String(currentUsourceSerial));
        });
        templateDomBits.find('input,select').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentUsourceSerial)); }
            if (this.name) { this.name = this.name.replace('bt', String(currentUsourceSerial)); }
        });
        templateDomBits.find('tr').each(function () {
            if (this.id) { this.id = this.id.replace('bt', String(currentUsourceSerial)); }
        });
        templateDomBits.find('select').change();
        templateDomBits.children().appendTo('#pdusource > tbody');
        
        // hide the no entries found message
        jQuery('#pdusource-empty').hide();
    });
});

// given a project path (i.e. /project/foo) and version id, redirect to the 
// proper edit version page
function editVersionRedirect(projectPath, versionId) {
                
    if(versionId >= 0) {
    
       // makes sure projectPath ends in slash
       if(projectPath.charAt(projectPath.length -1) != '/') {
           projectPath += '/';
       }
    
       location = projectPath + 'editVersion?id=' + versionId;
    }
}
