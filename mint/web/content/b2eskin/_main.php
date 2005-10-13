<?php
	/**
	 * This is the main template. It displays the blog.
	 *
	 * However this file is not meant to be called directly.
	 * It is meant to be called automagically by b2evolution.
	 * To display a blog, you should call a stub file instead, for example:
	 * /blogs/index.php or /blogs/blog_b.php
	 *
	 * b2evolution - {@link http://b2evolution.net/}
	 * Released under GNU GPL License - {@link http://b2evolution.net/about/license.html}
	 * @copyright (c)2003-2004 by Francois PLANQUE - {@link http://fplanque.net/}
	 *
	 * @package evoskins
	 * @subpackage basic
	 */
if( !defined('DB_USER') ) die( 'Please, do not access this page directly.' );
?>
<html>
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=<?php locale_charset() ?>" />
        <script src="http://www.rpath.org/conary-static//apps/mint/javascript/generic.js" type="text/javascript" />
        <script src="http://www.rpath.org/conary-static//apps/mint/javascript/library.js" type="text/javascript" />
        <script src="http://www.rpath.org/conary-static//apps/mint/javascript/xmlrpc.js" type="text/javascript" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/basic.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/structure.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/user.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/topNav.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/log.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/contentTypes.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/mint.css" type="text/css" rel="stylesheet" />

        <link href="http://www.rpath.org/favicon.ico" rel="shortcut icon" />
        <link href="http://www.rpath.org/favicon.ico" rel="icon" />

	<title><?php
		$Blog->disp('name', 'htmlhead');
		single_cat_title( ' - ', 'htmlhead' );
		single_month_title( ' - ', 'htmlhead' );
		single_post_title( ' - ', 'htmlhead' );
		arcdir_title( ' - ', 'htmlhead' );
		profile_title( ' - ', 'htmlhead' );
	?>
	</title>
	<base href="<?php skinbase(); // Base URL for this skin. You need this to fix relative links! ?>" />
	<meta name="generator" content="b2evolution <?php echo $b2_version ?>" /> <!-- Please leave this for stats -->
</head>
<body xmlns="http://www.w3.org/1999/xhtml">

    <div align="center" id="top">
    <div class="shadowLeft"><div class="shadowRight">
        <div align="left" class="surfaceLeft"><div class="surfaceRight">
            <table cellpadding="0" cellspacing="0" border="0" summary="layout">
        <tr><td colspan="2"><div class="pad"><img src="http://www.rpath.org/conary-static/apps/mint/images/logo.gif"/></div></td>
</tr>
    <tr>
    <td id="topnav">
        <div class="pad">
            <a href="http://www.rpath.org/">Home</a> | 
    <?php
    /**
     * --------------------------- BLOG LIST INCLUDED HERE -----------------------------
     */
    require( dirname(__FILE__).'/_bloglist.php' );
    // ---------------------------------- END OF BLOG LIST --------------------------------- ?>
        </div>
    </td>
       	<td id="log">
            <div class="pad">
        <?php 
                    user_login_link( '', '' ); 
                    user_register_link( '', '' ); 
                    user_admin_link( '', '' ); 
                    user_profile_link( '', '' ); 
                    user_logout_link( '', '' ); 
            ?> </div> </td>    </tr>
        </table>
</div></div></div></div>
</div>

    <div align="center" id="middle">
        <div id="crumb">

            <div class="pad">
                You are here: <a href="http://www.rpath.org/">Home</a> <a href="#"><?php $Blog->disp('name', 'htmlbody')?></a>
            </div>
        </div>
    </div>
    <div align="center" id="bottom">
        <div class="shadowLeft"><div class="shadowRight">
            <div align="left" class="surfaceLeft"><div class="surfaceRight">

                <table cellpadding="0" cellspacing="0" border="0" width="100%" summary="layout">
                    <tr>
                        <td>
        <table cellpadding="0" border="0" summary="layout" cellspacing="0" width="100%">
            <tr>
                <td id="left" class="side">
                    <div class="pad">
    <div align="center">
<?php
            single_cat_title();
            single_month_title();
            single_post_title();
            arcdir_title();
            last_comments_title();
            stats_title();
            profile_title();
    ?>
    </div>	
    <div id="search" class="palette">
            <h3 class="sideItemTitle"><?php echo T_('Search') ?></h3>
            <?php form_formstart( $Blog->dget( 'blogurl', 'raw' ), 'search', 'SearchForm' ) ?>
                    <p><input type="text" name="s" size="30" value="<?php echo htmlspecialchars($s) ?>" class="SearchField" /><br />
                    <input type="radio" style="width:auto;" name="sentence" value="AND" id="sentAND" <?php if( $sentence=='AND' ) echo 'checked="checked" ' ?>/><label for="sentAND"><?php echo T_('All Words') ?></label><br />
                    <input type="radio" style="width:auto;" name="sentence" value="OR" id="sentOR" <?php if( $sentence=='OR' ) echo 'checked="checked" ' ?>/><label for="sentOR"><?php echo T_('Some Word') ?></label><br />
                    <input type="radio" style="width:auto;" name="sentence" value="sentence" id="sentence" <?php if( $sentence=='sentence' ) echo 'checked="checked" ' ?>/><label for="sentence"><?php echo T_('Entire phrase') ?></label></p>
                    <button type="submit" name="submit" class="submit"><?php echo T_('Search') ?></button>
            </form>
    </div>
                    </div>
                </td>
    <td id="main">
        <div class="pad">

    <?php	// ---------------------------------- START OF POSTS --------------------------------------
    if( isset($MainList) ) $MainList->display_if_empty();	// Display message if no post

    if( isset($MainList) ) while( $Item = $MainList->get_item() )
    {
            $MainList->date_if_changed();
            $Item->anchor(); 
            locale_temp_switch( $Item->locale ); // Temporarily switch to post locale
            ?>
            <div class="newsItem">
                <h3>
                    <span style="float: right;" class="date">
                        <?php $Item->issue_time(); ?>
                        <a href="<?php $Item->permalink() ?>" 
                           title="<?php echo T_('Permanent link to full entry') ?>">
                            <img src="img/icon_minipost.gif" alt="Permalink" width="12" height="9" border="0" align="middle" />
                        </a>
                    </span>
                    <span class="newsTitle"><?php $Item->title(); ?></span>
                </h3>

                <blockquote style="margin-left: 1em;">

                        <div>
                                <?php $Item->content( '#', '#', T_('Read more...') ); ?>
                                <?php link_pages() ?>
                        </div>

                        <small>

                        <?php $Item->feedback_link( 'feedbacks', '', ' &bull; ' ) // Link to comments, trackback... ?>

                        <?php $Item->edit_link( '', ' ' ) // Link to backoffice for editing ?>

                        </small>

                </blockquote>
            </div>

            <?php	// ------------- START OF INCLUDE FOR COMMENTS, TRACKBACK, PINGBACK, ETC. --------------
            $disp_comments = 1;					// Display the comments if requested
            $disp_comment_form = 1;			// Display the comments form if comments requested
            $disp_trackbacks = 1;				// Display the trackbacks if requested

            $disp_trackback_url = 1;		// Display the trackbal URL if trackbacks requested
            $disp_pingbacks = 1;				// Display the pingbacks if requested
            require( dirname(__FILE__).'/_feedback.php' );
            // ----------------- END OF INCLUDE FOR COMMENTS, TRACKBACK, PINGBACK, ETC. ----------------- 

            locale_restore_previous();	// Restore previous locale (Blog locale)
            ?>
    <?php } // --------------------------------- END OF POSTS ----------------------------------- ?> 

    <?php // ---------------- START OF INCLUDES FOR LAST COMMENTS, STATS ETC. ----------------
            switch( $disp )
            {
                    case 'arcdir':
                            // this includes the archive directory if requested
                            require( dirname(__FILE__).'/_arcdir.php');
                            break;
    
                    case 'profile':
                            // this includes the profile form if requested
                            require( dirname(__FILE__).'/_profile.php');
                            break;
            }
            // ------------------- END OF INCLUDES FOR LAST COMMENTS, STATS ETC. ------------------- ?>

    <div align="center" style="margin-bottom: 0.5em;">
            <strong>
            <?php posts_nav_link(); ?>
            ::
            <a href="<?php $Blog->disp( 'arcdirurl', 'raw' ) ?>"><?php echo T_('Archives') ?></a>
            </strong>
    </div>

</td>
<td id="right" class="projects">	
<div class="pad">
    <div class="bSideItem">
            <h3><?php $Blog->disp( 'name', 'htmlbody' ) ?></h3>
            <p><?php $Blog->disp( 'longdesc', 'htmlbody' ); ?></p>
            <!--?php next_post(); // activate this if you want a link to the next post in single page mode ?-->
            <!--?php previous_post(); // activate this if you want a link to the previous post in single page mode ?-->
            <?php // -------------------------- CALENDAR INCLUDED HERE -----------------------------
                    require( dirname(__FILE__).'/_calendar.php' );
                    // -------------------------------- END OF CALENDAR ---------------------------------- ?>
    </div>

    <?php if( ! $Blog->get('force_skin') )
    {	// Skin switching is allowed for this blog: ?>
            <div class="bSideItem">
                    <h3><?php echo T_('Choose skin') ?></h3>
                    <ul>
                            <?php // ------------------------------- START OF SKIN LIST -------------------------------
                            for( skin_list_start(); skin_list_next(); ) { ?>
                                    <li><a href="<?php skin_change_url() ?>"><?php skin_list_iteminfo( 'name', 'htmlbody' ) ?></a></li>
                            <?php } // ------------------------------ END OF SKIN LIST ------------------------------ ?>
                    </ul>
            </div>
    <?php } ?>
    
    <?php if (false) 
    { ?>
    <div class="bSideItem">
            <h3><?php echo T_('Recent Referers') ?></h3>
                    <?php refererList(5, 'global', 0, 0, 'no', '', ($blog > 1) ? $blog : ''); ?>
                    <ul>
                            <?php if( count( $res_stats ) ) foreach( $res_stats as $row_stats ) { ?>
                                    <li><a href="<?php stats_referer() ?>"><?php stats_basedomain() ?></a></li>
                            <?php } // End stat loop ?>
                            <li><a href="<?php $Blog->disp( 'blogstatsurl', 'raw' ) ?>"><?php echo T_('more...') ?></a></li>
                    </ul>
            <br />
            <h3><?php echo T_('Top Referers') ?></h3>
                    <?php refererList(5, 'global', 0, 0, 'no', 'baseDomain', ($blog > 1) ? $blog : ''); ?>
                    <ul>
                            <?php if( count( $res_stats ) ) foreach( $res_stats as $row_stats ) { ?>
                                    <li><a href="<?php stats_referer() ?>"><?php stats_basedomain() ?></a></li>
                            <?php } // End stat loop ?>
                            <li><a href="<?php $Blog->disp( 'blogstatsurl', 'raw' ) ?>"><?php echo T_('more...') ?></a></li>
                    </ul>
    </div>

    <?php } ?>


	<div class="bSideItem">
		<h3><?php echo T_('Syndicate this blog') ?> <img src="../../img/xml.gif" alt="XML" width="36" height="14" class="middle" /></h3>
			<ul>
				<li>
					RSS 0.92:
					<a href="<?php $Blog->disp( 'rss_url', 'raw' ) ?>"><?php echo T_('Posts') ?></a>,
					<a href="<?php $Blog->disp( 'comments_rss_url', 'raw' ) ?>"><?php echo T_('Comments') ?></a>
				</li>
				<li>
					RSS 1.0:
					<a href="<?php $Blog->disp( 'rdf_url', 'raw' ) ?>"><?php echo T_('Posts') ?></a>,
					<a href="<?php $Blog->disp( 'comments_rdf_url', 'raw' ) ?>"><?php echo T_('Comments') ?></a>
				</li>
				<li>
					RSS 2.0:
					<a href="<?php $Blog->disp( 'rss2_url', 'raw' ) ?>"><?php echo T_('Posts') ?></a>,
					<a href="<?php $Blog->disp( 'comments_rss2_url', 'raw' ) ?>"><?php echo T_('Comments') ?></a>
				</li>
				<li>
					Atom:
					<a href="<?php $Blog->disp( 'atom_url', 'raw' ) ?>"><?php echo T_('Posts') ?></a>,
					<a href="<?php $Blog->disp( 'comments_atom_url', 'raw' ) ?>"><?php echo T_('Comments') ?></a>
				</li>
			</ul>
	</div>
     </div>
</td>
</tr>
</table>
</td>
</tr>
</table>
</div>
</div>
</div>
</div>
</div>
<div align="center" id="foot">
            <div id="copy">
                <div style="text-align: center;" class="pad">
                    <span id="botnav">
                        <a href="#" onclick="javascript:{window.open('http://www.rpath.org/legal?page=legal', 'legal',          'height=500,width=500,menubar=no,scrollbars,status=no,toolbar=no', true); return false;}">Legal</a>
                    </span>
                    <span style="float: left;">Copyright © 2005 rPath, Inc. </span>
                </div> 
            </div>
	<?php 
		log_hit();	// log the hit on this page
		debug_info();	// output debug info if requested
	?>
</body>
</html>
