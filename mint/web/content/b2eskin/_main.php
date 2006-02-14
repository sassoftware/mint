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
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head>
        <base href="<?php skinbase(); // Base URL for this skin. You need this to fix relative links! ?>" />
        <meta http-equiv="Content-Type" content="text/html; charset=<?php locale_charset() ?>" />
        <meta name="generator" content="b2evolution <?php echo $b2_version ?>" /> <!-- Please leave this for stats -->
        <link href="http://www.rpath.org/conary-static/apps/mint/css/contentTypes.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/conary-static/apps/mint/css/mint.css" type="text/css" rel="stylesheet" />
        <link href="css/blog.css" type="text/css" rel="stylesheet" />
        <link href="http://www.rpath.org/favicon.ico" rel="shortcut icon" />
        <link href="<?php $Blog->disp( 'rss2_url', 'raw' ) ?>" type="application/rss+xml" rel="alternate" title="<?php $Blog->disp('name', 'raw' ) ?>" />
        <link href="http://www.rpath.org/favicon.ico" rel="icon" />
        <title><?php
            $Blog->disp('name', 'htmlhead');
            single_cat_title( ' - ', 'htmlhead' );
            single_month_title( ' - ', 'htmlhead' );
            single_post_title( ' - ', 'htmlhead' );
            arcdir_title( ' - ', 'htmlhead' );
            profile_title( ' - ', 'htmlhead' );
        ?></title>
    </head>
    <body>
        <div id="main">
            <!-- header -->
            <a name="#top" />
            <div id="top">
                <img id="topgradleft" src="http://www.rpath.com/conary-static/apps/mint/images/topgrad_left.png" alt="" />
                <img id="topgradright" src="http://www.rpath.com/conary-static/apps/mint/images/topgrad_right.png" alt="" />
                <div id="corpLogo">
                    <a href="http://www.rpath.com/">
                        <img src="http://www.rpath.com/conary-static/apps/mint/images/corplogo_notrans.png" width="80" height="98" alt="rPath Logo" />
                    </a>
                </div>
                <div id="prodLogo">
                    <a href="http://www.rpath.com/">
                        <img src="http://www.rpath.com/corp/images/logotype.gif" alt="rPath. The Software Appliance Company." />
                    </a>
                </div>
                <div id="topRight">
                    <div class="about"><a href="http://www.rpath.com/corp/">About rPath</a>
                    </div>
                    <form action="http://www.rpath.com/search" method="get" id="searchForm">
                        <div>
                            <label class="search" for="searchLabel">I'm looking for a...</label>
                            <input class="search" name="search" id="searchLabel" type="text" />
                            <button class="img" id="searchSubmit" type="submit"><img src="http://www.rpath.com/conary-static/apps/mint/images/search.png" alt="Search" /></button><br />
                            <input id="typeProject" type="radio" name="type" value="Projects" checked="checked" />
                            <label for="typeProject">Project</label>
                            <input id="typePackage" type="radio" name="type" value="Packages" />
                            <label for="typePackage">Package</label>
                            <span id="browseText">&nbsp;&nbsp;&nbsp;Or you can <a href="http://www.rpath.com/projects">browse</a>.</span>
                        </div>
                    </form>
                </div>
            </div>
            
            <div class="layout">
                <div id="left" class="side">
                    <?php
                        /**
                         * --------------------------- BLOG LIST INCLUDED HERE -----------------------------
                         */
                        require( dirname(__FILE__).'/_bloglist.php' );
                        // ---------------------------------- END OF BLOG LIST --------------------------------- 
                    ?>
                    <!-- <div class="pad">
                        <div id="search" class="palette">
                            <h3 class="sideItemTitle"><?php echo T_('Search') ?></h3>
                                <?php form_formstart( $Blog->dget( 'blogurl', 'raw' ), 'search', 'SearchForm' ) ?>
                                <p><input type="text" name="s" size="30" value="<?php echo htmlspecialchars($s) ?>" class="SearchField" /><br />
                                <input type="radio" style="width:auto; background-color: #e6e6e6;" name="sentence" value="AND" id="sentAND" <?php if( $sentence=='AND' ) echo 'checked="checked" ' ?>/><label for="sentAND"><?php echo T_('All Words') ?></label><br />
                                <input type="radio" style="width:auto; background-color: #e6e6e6;" name="sentence" value="OR" id="sentOR" <?php if( $sentence=='OR' ) echo 'checked="checked" ' ?>/><label for="sentOR"><?php echo T_('Some Word') ?></label><br />
                                <input type="radio" style="width:auto; background-color: #e6e6e6;" name="sentence" value="sentence" id="sentence" <?php if( $sentence=='sentence' ) echo 'checked="checked" ' ?>/><label for="sentence"><?php echo T_('Entire phrase') ?></label></p>
                                <button type="submit" name="submit" class="submit"><?php echo T_('Search') ?></button>
                            </form>
                        </div>
                    </div> -->
                </div>
                <div id="right" class="side">
                    <div class="bSideItem">
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
                </div>
                <div id="middle">
                    <div class="news">
                        <div class="newsHeader">
                            <h1 class="blogTitle"><?php $Blog->disp( 'name', 'htmlbody' ) ?></h1>
                            <div class="blogDesc"><?php $Blog->disp( 'longdesc' ); ?>
                            <p><?php
                                single_cat_title();
                                single_month_title();
                                single_post_title();
                                arcdir_title();
                                last_comments_title();
                                stats_title();
                                profile_title();
                            ?></p>
                            </div>
                        </div>	
                        <?php	// ---------------------------------- START OF POSTS --------------------------------------
                        if( isset($MainList) ) $MainList->display_if_empty();	// Display message if no post

                        if( isset($MainList) ) while( $Item = $MainList->get_item() )
                        {
                            $MainList->date_if_changed('<div class="newsDate">','</div>','F j, Y'); 
                            $Item->anchor(); 
                            locale_temp_switch( $Item->locale ); // Temporarily switch to post locale
                        ?>
                        <div class="newsItem">
                            <div class="itemHeader">
                                <div class="itemByline">
                                    Posted by <?php $Item->Author->prefered_name() ?><br />
                                    <?php $Item->issue_time('g:i A'); ?>
                                </div>
                                <span class="itemTitle">
                                    <a href="<?php $Item->permalink() ?>" 
                                       title="<?php echo T_('Permanent link to full entry') ?>">
                                       <?php $Item->title(); ?>
                                    </a>
                                </span>
                            </div>
                            <div class="itemContent">
                                <?php $Item->content( '#', '#', T_('Read more...') ); ?>
                            </div>
                            <div class="itemFooter">
                                <?php link_pages() ?>
                                <?php $Item->feedback_link( 'feedbacks', '', ' &bull; ' ) // Link to comments, trackback... ?>
                                <?php $Item->edit_link( '', ' ' ) // Link to backoffice for editing ?>
                            </div>
                        </div>

                        <?php	// ------------- START OF INCLUDE FOR COMMENTS, TRACKBACK, PINGBACK, ETC. --------------
                            $disp_comments = 1;		// Display the comments if requested
                            $disp_comment_form = 1; // Display the comments form if comments requested
                            $disp_trackbacks = 1;   // Display the trackbacks if requested

                            $disp_trackback_url = 1;// Display the trackbal URL if trackbacks requested
                            $disp_pingbacks = 1;    // Display the pingbacks if requested
                            require( dirname(__FILE__).'/_feedback.php' ); // ----------------- END OF INCLUDE FOR COMMENTS, TRACKBACK, PINGBACK, ETC. ----------------- 

                            locale_restore_previous();	// Restore previous locale (Blog locale)
                        ?>
                        <?php } // --------------------------------- END OF POSTS ----------------------------------- ?> 


                        <div class="newsFooter">
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

                            <strong>
                                <?php posts_nav_link(); ?>
                                ::
                                <a href="<?php $Blog->disp( 'arcdirurl', 'raw' ) ?>"><?php echo T_('Archives') ?></a>
                            </strong>
                        </div>
                    </div>
                </div>
            </div>
            <div id="footer">
                <div>
                    <span id="topOfPage"><a href="#top">Top of Page</a></span>
                    <ul class="footerLinks">
                        <li><a href="http://www.rpath.com/corp/">About rPath</a></li>
                        <li><a href="http://www.rpath.com/legal/">Legal</a></li>
                        <li><a href="http://www.rpath.com/corp/company-contact-rpath.html">Contact Us</a></li>
                        <li><a href="http://www.rpath.com/help/">Help</a></li>
                    </ul>
                </div>
                <div id="bottomText">
                    <span id="copyright">Copyright &copy; 2005-2006 rPath. All Rights Reserved.</span>
                    <span id="tagline">rPath. The Software Appliance Company.</span>
                </div>
                <div id="b2elinks">
                    <ul>
                        <li><strong>b2e administration</strong></li>
                        <?php user_login_link( '<li>', '</li>' ); ?>
                        <?php user_register_link( '<li>', '</li>' ); ?>
                        <?php user_admin_link( '<li>', '</li>' ); ?>
                        <?php user_profile_link( '<li>', '</li>' ); ?>
                        <?php user_logout_link( '<li>', '</li>' ); ?>
                    </ul>
                </div>
            </div>
        </div>
        <?php 
            log_hit();	    // log the hit on this page
            debug_info();	// output debug info if requested
        ?>
    </body>
</html>
