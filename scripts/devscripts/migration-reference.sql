--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: appliancespotlight; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE appliancespotlight (
    itemid integer NOT NULL,
    title character varying(255),
    text character varying(255),
    link character varying(255),
    logo character varying(255),
    showarchive integer,
    startdate integer,
    enddate integer
);


ALTER TABLE public.appliancespotlight OWNER TO conary;

--
-- Name: appliancespotlight_itemid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE appliancespotlight_itemid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.appliancespotlight_itemid_seq OWNER TO conary;

--
-- Name: appliancespotlight_itemid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE appliancespotlight_itemid_seq OWNED BY appliancespotlight.itemid;


--
-- Name: appliancespotlight_itemid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('appliancespotlight_itemid_seq', 1, false);


--
-- Name: builddata; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE builddata (
    buildid integer NOT NULL,
    name character varying(32) NOT NULL,
    value text NOT NULL,
    datatype smallint NOT NULL
);


ALTER TABLE public.builddata OWNER TO conary;

--
-- Name: buildfiles; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE buildfiles (
    fileid integer NOT NULL,
    buildid integer NOT NULL,
    idx smallint DEFAULT 0 NOT NULL,
    title character varying(255) DEFAULT ''::character varying NOT NULL,
    size bigint,
    sha1 character(40)
);


ALTER TABLE public.buildfiles OWNER TO conary;

--
-- Name: buildfiles_fileid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE buildfiles_fileid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.buildfiles_fileid_seq OWNER TO conary;

--
-- Name: buildfiles_fileid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE buildfiles_fileid_seq OWNED BY buildfiles.fileid;


--
-- Name: buildfiles_fileid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('buildfiles_fileid_seq', 1, false);


--
-- Name: buildfilesurlsmap; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE buildfilesurlsmap (
    fileid integer NOT NULL,
    urlid integer NOT NULL
);


ALTER TABLE public.buildfilesurlsmap OWNER TO conary;

--
-- Name: builds; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE builds (
    buildid integer NOT NULL,
    projectid integer NOT NULL,
    pubreleaseid integer,
    buildtype integer,
    job_uuid uuid,
    name character varying(255),
    description text,
    trovename character varying(128),
    troveversion character varying(255),
    troveflavor character varying(4096),
    trovelastchanged numeric(14,3),
    timecreated numeric(14,3),
    createdby integer,
    timeupdated numeric(14,3),
    updatedby integer,
    buildcount integer DEFAULT 0 NOT NULL,
    productversionid integer,
    stagename character varying(255) DEFAULT ''::character varying,
    status integer DEFAULT (-1),
    statusmessage text DEFAULT ''::text
);


ALTER TABLE public.builds OWNER TO conary;

--
-- Name: builds_buildid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE builds_buildid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.builds_buildid_seq OWNER TO conary;

--
-- Name: builds_buildid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE builds_buildid_seq OWNED BY builds.buildid;


--
-- Name: builds_buildid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('builds_buildid_seq', 1, false);


--
-- Name: changelog_change_log; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE changelog_change_log (
    change_log_id integer NOT NULL,
    resource_type text NOT NULL,
    resource_id integer NOT NULL
);


ALTER TABLE public.changelog_change_log OWNER TO conary;

--
-- Name: changelog_change_log_change_log_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE changelog_change_log_change_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.changelog_change_log_change_log_id_seq OWNER TO conary;

--
-- Name: changelog_change_log_change_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE changelog_change_log_change_log_id_seq OWNED BY changelog_change_log.change_log_id;


--
-- Name: changelog_change_log_change_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('changelog_change_log_change_log_id_seq', 1, false);


--
-- Name: changelog_change_log_entry; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE changelog_change_log_entry (
    change_log_entry_id integer NOT NULL,
    change_log_id integer NOT NULL,
    entry_text text NOT NULL,
    entry_date timestamp with time zone NOT NULL
);


ALTER TABLE public.changelog_change_log_entry OWNER TO conary;

--
-- Name: changelog_change_log_entry_change_log_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE changelog_change_log_entry_change_log_entry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.changelog_change_log_entry_change_log_entry_id_seq OWNER TO conary;

--
-- Name: changelog_change_log_entry_change_log_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE changelog_change_log_entry_change_log_entry_id_seq OWNED BY changelog_change_log_entry.change_log_entry_id;


--
-- Name: changelog_change_log_entry_change_log_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('changelog_change_log_entry_change_log_entry_id_seq', 1, false);


--
-- Name: ci_rhn_channel_package; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_channel_package (
    channel_id integer NOT NULL,
    package_id integer NOT NULL
);


ALTER TABLE public.ci_rhn_channel_package OWNER TO conary;

--
-- Name: ci_rhn_channels; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_channels (
    channel_id integer NOT NULL,
    label character varying(256) NOT NULL,
    last_modified character varying
);


ALTER TABLE public.ci_rhn_channels OWNER TO conary;

--
-- Name: ci_rhn_channels_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE ci_rhn_channels_channel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ci_rhn_channels_channel_id_seq OWNER TO conary;

--
-- Name: ci_rhn_channels_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE ci_rhn_channels_channel_id_seq OWNED BY ci_rhn_channels.channel_id;


--
-- Name: ci_rhn_channels_channel_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('ci_rhn_channels_channel_id_seq', 1, false);


--
-- Name: ci_rhn_errata; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_errata (
    errata_id integer NOT NULL,
    advisory character varying NOT NULL,
    advisory_type character varying NOT NULL,
    issue_date character varying NOT NULL,
    last_modified_date character varying NOT NULL,
    synopsis character varying NOT NULL,
    update_date character varying NOT NULL
);


ALTER TABLE public.ci_rhn_errata OWNER TO conary;

--
-- Name: ci_rhn_errata_channel; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_errata_channel (
    errata_id integer NOT NULL,
    channel_id integer NOT NULL
);


ALTER TABLE public.ci_rhn_errata_channel OWNER TO conary;

--
-- Name: ci_rhn_errata_errata_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE ci_rhn_errata_errata_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ci_rhn_errata_errata_id_seq OWNER TO conary;

--
-- Name: ci_rhn_errata_errata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE ci_rhn_errata_errata_id_seq OWNED BY ci_rhn_errata.errata_id;


--
-- Name: ci_rhn_errata_errata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('ci_rhn_errata_errata_id_seq', 1, false);


--
-- Name: ci_rhn_errata_nevra_channel; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_errata_nevra_channel (
    errata_id integer NOT NULL,
    nevra_id integer NOT NULL,
    channel_id integer NOT NULL
);


ALTER TABLE public.ci_rhn_errata_nevra_channel OWNER TO conary;

--
-- Name: ci_rhn_nevra; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_nevra (
    nevra_id integer NOT NULL,
    name character varying NOT NULL,
    epoch integer NOT NULL,
    version character varying NOT NULL,
    release character varying NOT NULL,
    arch character varying NOT NULL
);


ALTER TABLE public.ci_rhn_nevra OWNER TO conary;

--
-- Name: ci_rhn_nevra_nevra_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE ci_rhn_nevra_nevra_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ci_rhn_nevra_nevra_id_seq OWNER TO conary;

--
-- Name: ci_rhn_nevra_nevra_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE ci_rhn_nevra_nevra_id_seq OWNED BY ci_rhn_nevra.nevra_id;


--
-- Name: ci_rhn_nevra_nevra_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('ci_rhn_nevra_nevra_id_seq', 1, false);


--
-- Name: ci_rhn_package_failed; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_package_failed (
    package_failed_id integer NOT NULL,
    package_id integer NOT NULL,
    failed_timestamp integer NOT NULL,
    failed_msg character varying NOT NULL,
    resolved character varying
);


ALTER TABLE public.ci_rhn_package_failed OWNER TO conary;

--
-- Name: ci_rhn_package_failed_package_failed_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE ci_rhn_package_failed_package_failed_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ci_rhn_package_failed_package_failed_id_seq OWNER TO conary;

--
-- Name: ci_rhn_package_failed_package_failed_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE ci_rhn_package_failed_package_failed_id_seq OWNED BY ci_rhn_package_failed.package_failed_id;


--
-- Name: ci_rhn_package_failed_package_failed_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('ci_rhn_package_failed_package_failed_id_seq', 1, false);


--
-- Name: ci_rhn_packages; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_rhn_packages (
    package_id integer NOT NULL,
    nevra_id integer NOT NULL,
    md5sum character varying,
    sha1sum character varying,
    last_modified character varying NOT NULL,
    path character varying
);


ALTER TABLE public.ci_rhn_packages OWNER TO conary;

--
-- Name: ci_rhn_packages_package_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE ci_rhn_packages_package_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ci_rhn_packages_package_id_seq OWNER TO conary;

--
-- Name: ci_rhn_packages_package_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE ci_rhn_packages_package_id_seq OWNED BY ci_rhn_packages.package_id;


--
-- Name: ci_rhn_packages_package_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('ci_rhn_packages_package_id_seq', 1, false);


--
-- Name: ci_yum_packages; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_yum_packages (
    package_id integer NOT NULL,
    nevra_id integer NOT NULL,
    sha1sum character varying,
    checksum character varying NOT NULL,
    checksum_type character varying NOT NULL,
    path character varying
);


ALTER TABLE public.ci_yum_packages OWNER TO conary;

--
-- Name: ci_yum_packages_package_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE ci_yum_packages_package_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ci_yum_packages_package_id_seq OWNER TO conary;

--
-- Name: ci_yum_packages_package_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE ci_yum_packages_package_id_seq OWNED BY ci_yum_packages.package_id;


--
-- Name: ci_yum_packages_package_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('ci_yum_packages_package_id_seq', 1, false);


--
-- Name: ci_yum_repositories; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_yum_repositories (
    yum_repository_id integer NOT NULL,
    label character varying(256) NOT NULL,
    "timestamp" character varying,
    checksum character varying,
    checksum_type character varying
);


ALTER TABLE public.ci_yum_repositories OWNER TO conary;

--
-- Name: ci_yum_repositories_yum_repository_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE ci_yum_repositories_yum_repository_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.ci_yum_repositories_yum_repository_id_seq OWNER TO conary;

--
-- Name: ci_yum_repositories_yum_repository_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE ci_yum_repositories_yum_repository_id_seq OWNED BY ci_yum_repositories.yum_repository_id;


--
-- Name: ci_yum_repositories_yum_repository_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('ci_yum_repositories_yum_repository_id_seq', 1, false);


--
-- Name: ci_yum_repository_package; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE ci_yum_repository_package (
    yum_repository_id integer NOT NULL,
    package_id integer NOT NULL,
    location character varying NOT NULL
);


ALTER TABLE public.ci_yum_repository_package OWNER TO conary;

--
-- Name: commits; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE commits (
    projectid integer NOT NULL,
    "timestamp" numeric(14,3),
    trovename character varying(255),
    version character varying(255),
    userid integer
);


ALTER TABLE public.commits OWNER TO conary;

--
-- Name: communityids; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE communityids (
    projectid integer NOT NULL,
    communitytype integer,
    communityid character varying(255)
);


ALTER TABLE public.communityids OWNER TO conary;

--
-- Name: confirmations; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE confirmations (
    userid integer NOT NULL,
    timerequested integer,
    confirmation character varying(255)
);


ALTER TABLE public.confirmations OWNER TO conary;

--
-- Name: databaseversion; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE databaseversion (
    version integer,
    minor integer
);


ALTER TABLE public.databaseversion OWNER TO conary;

--
-- Name: django_redirect; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE django_redirect (
    id integer NOT NULL,
    site_id integer NOT NULL,
    old_path character varying(200) NOT NULL,
    new_path character varying(200) NOT NULL
);


ALTER TABLE public.django_redirect OWNER TO conary;

--
-- Name: django_redirect_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE django_redirect_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.django_redirect_id_seq OWNER TO conary;

--
-- Name: django_redirect_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE django_redirect_id_seq OWNED BY django_redirect.id;


--
-- Name: django_redirect_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('django_redirect_id_seq', 1, false);


--
-- Name: django_site; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE django_site (
    id integer NOT NULL,
    domain character varying(100) NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.django_site OWNER TO conary;

--
-- Name: django_site_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE django_site_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.django_site_id_seq OWNER TO conary;

--
-- Name: django_site_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE django_site_id_seq OWNED BY django_site.id;


--
-- Name: django_site_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('django_site_id_seq', 1, false);


--
-- Name: filesurls; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE filesurls (
    urlid integer NOT NULL,
    urltype smallint NOT NULL,
    url character varying(255) NOT NULL
);


ALTER TABLE public.filesurls OWNER TO conary;

--
-- Name: filesurls_urlid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE filesurls_urlid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.filesurls_urlid_seq OWNER TO conary;

--
-- Name: filesurls_urlid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE filesurls_urlid_seq OWNED BY filesurls.urlid;


--
-- Name: filesurls_urlid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('filesurls_urlid_seq', 1, false);


--
-- Name: frontpageselections; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE frontpageselections (
    itemid integer NOT NULL,
    name character varying(255),
    link character varying(255),
    rank integer
);


ALTER TABLE public.frontpageselections OWNER TO conary;

--
-- Name: frontpageselections_itemid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE frontpageselections_itemid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.frontpageselections_itemid_seq OWNER TO conary;

--
-- Name: frontpageselections_itemid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE frontpageselections_itemid_seq OWNED BY frontpageselections.itemid;


--
-- Name: frontpageselections_itemid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('frontpageselections_itemid_seq', 1, false);


--
-- Name: inboundmirrors; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inboundmirrors (
    inboundmirrorid integer NOT NULL,
    targetprojectid integer NOT NULL,
    sourcelabels character varying(767) NOT NULL,
    sourceurl character varying(767) NOT NULL,
    sourceauthtype character varying(32) NOT NULL,
    sourceusername character varying(254),
    sourcepassword character varying(254),
    sourceentitlement character varying(254),
    mirrororder integer DEFAULT 0,
    alllabels integer DEFAULT 0
);


ALTER TABLE public.inboundmirrors OWNER TO conary;

--
-- Name: inboundmirrors_inboundmirrorid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inboundmirrors_inboundmirrorid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inboundmirrors_inboundmirrorid_seq OWNER TO conary;

--
-- Name: inboundmirrors_inboundmirrorid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inboundmirrors_inboundmirrorid_seq OWNED BY inboundmirrors.inboundmirrorid;


--
-- Name: inboundmirrors_inboundmirrorid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inboundmirrors_inboundmirrorid_seq', 1, false);


--
-- Name: inventory_event_type; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_event_type (
    event_type_id integer NOT NULL,
    name character varying(8092) NOT NULL,
    description character varying(8092) NOT NULL,
    priority smallint NOT NULL
);


ALTER TABLE public.inventory_event_type OWNER TO conary;

--
-- Name: inventory_event_type_event_type_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_event_type_event_type_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_event_type_event_type_id_seq OWNER TO conary;

--
-- Name: inventory_event_type_event_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_event_type_event_type_id_seq OWNED BY inventory_event_type.event_type_id;


--
-- Name: inventory_event_type_event_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_event_type_event_type_id_seq', 11, true);


--
-- Name: inventory_job; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_job (
    job_id integer NOT NULL,
    job_uuid character varying(64) NOT NULL,
    job_state_id integer NOT NULL,
    event_type_id integer NOT NULL,
    status_code integer DEFAULT 100 NOT NULL,
    status_text character varying DEFAULT 'Initializing'::character varying NOT NULL,
    status_detail character varying,
    time_created timestamp with time zone NOT NULL,
    time_updated timestamp with time zone NOT NULL
);


ALTER TABLE public.inventory_job OWNER TO conary;

--
-- Name: inventory_job_job_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_job_job_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_job_job_id_seq OWNER TO conary;

--
-- Name: inventory_job_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_job_job_id_seq OWNED BY inventory_job.job_id;


--
-- Name: inventory_job_job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_job_job_id_seq', 1, false);


--
-- Name: inventory_job_state; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_job_state (
    job_state_id integer NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.inventory_job_state OWNER TO conary;

--
-- Name: inventory_job_state_job_state_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_job_state_job_state_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_job_state_job_state_id_seq OWNER TO conary;

--
-- Name: inventory_job_state_job_state_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_job_state_job_state_id_seq OWNED BY inventory_job_state.job_state_id;


--
-- Name: inventory_job_state_job_state_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_job_state_job_state_id_seq', 4, true);


--
-- Name: inventory_management_interface; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_management_interface (
    management_interface_id integer NOT NULL,
    name character varying(8092) NOT NULL,
    description character varying(8092) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    port integer NOT NULL,
    credentials_descriptor text NOT NULL,
    credentials_readonly boolean
);


ALTER TABLE public.inventory_management_interface OWNER TO conary;

--
-- Name: inventory_management_interface_management_interface_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_management_interface_management_interface_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_management_interface_management_interface_id_seq OWNER TO conary;

--
-- Name: inventory_management_interface_management_interface_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_management_interface_management_interface_id_seq OWNED BY inventory_management_interface.management_interface_id;


--
-- Name: inventory_management_interface_management_interface_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_management_interface_management_interface_id_seq', 2, true);


--
-- Name: inventory_stage; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_stage (
    stage_id integer NOT NULL,
    name character varying(256) NOT NULL,
    label text NOT NULL,
    major_version_id integer
);


ALTER TABLE public.inventory_stage OWNER TO conary;

--
-- Name: inventory_stage_stage_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_stage_stage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_stage_stage_id_seq OWNER TO conary;

--
-- Name: inventory_stage_stage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_stage_stage_id_seq OWNED BY inventory_stage.stage_id;


--
-- Name: inventory_stage_stage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_stage_stage_id_seq', 1, false);


--
-- Name: inventory_system; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system (
    system_id integer NOT NULL,
    name character varying(8092) NOT NULL,
    description character varying(8092),
    created_date timestamp with time zone NOT NULL,
    hostname character varying(8092),
    launch_date timestamp with time zone,
    target_id integer,
    target_system_id character varying(255),
    target_system_name character varying(255),
    target_system_description character varying(1024),
    target_system_state character varying(64),
    registration_date timestamp with time zone,
    generated_uuid character varying(64),
    local_uuid character varying(64),
    ssl_client_certificate character varying(8092),
    ssl_client_key character varying(8092),
    ssl_server_certificate character varying(8092),
    agent_port integer,
    state_change_date timestamp with time zone,
    launching_user_id integer,
    current_state_id integer NOT NULL,
    managing_zone_id integer NOT NULL,
    management_interface_id integer,
    system_type_id integer,
    credentials text,
    configuration text,
    stage_id integer,
    major_version_id integer,
    appliance_id integer
);


ALTER TABLE public.inventory_system OWNER TO conary;

--
-- Name: inventory_system_event; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_event (
    system_event_id integer NOT NULL,
    system_id integer NOT NULL,
    event_type_id integer NOT NULL,
    time_created timestamp with time zone NOT NULL,
    time_enabled timestamp with time zone NOT NULL,
    priority smallint NOT NULL,
    event_data character varying
);


ALTER TABLE public.inventory_system_event OWNER TO conary;

--
-- Name: inventory_system_event_system_event_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_event_system_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_event_system_event_id_seq OWNER TO conary;

--
-- Name: inventory_system_event_system_event_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_event_system_event_id_seq OWNED BY inventory_system_event.system_event_id;


--
-- Name: inventory_system_event_system_event_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_event_system_event_id_seq', 1, false);


--
-- Name: inventory_system_installed_software; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_installed_software (
    id integer NOT NULL,
    system_id integer NOT NULL,
    trove_id integer NOT NULL
);


ALTER TABLE public.inventory_system_installed_software OWNER TO conary;

--
-- Name: inventory_system_installed_software_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_installed_software_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_installed_software_id_seq OWNER TO conary;

--
-- Name: inventory_system_installed_software_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_installed_software_id_seq OWNED BY inventory_system_installed_software.id;


--
-- Name: inventory_system_installed_software_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_installed_software_id_seq', 1, false);


--
-- Name: inventory_system_job; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_job (
    system_job_id integer NOT NULL,
    job_id integer NOT NULL,
    system_id integer NOT NULL,
    event_uuid character varying(64) NOT NULL
);


ALTER TABLE public.inventory_system_job OWNER TO conary;

--
-- Name: inventory_system_job_system_job_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_job_system_job_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_job_system_job_id_seq OWNER TO conary;

--
-- Name: inventory_system_job_system_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_job_system_job_id_seq OWNED BY inventory_system_job.system_job_id;


--
-- Name: inventory_system_job_system_job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_job_system_job_id_seq', 1, false);


--
-- Name: inventory_system_log; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_log (
    system_log_id integer NOT NULL,
    system_id integer NOT NULL
);


ALTER TABLE public.inventory_system_log OWNER TO conary;

--
-- Name: inventory_system_log_entry; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_log_entry (
    system_log_entry_id integer NOT NULL,
    system_log_id integer NOT NULL,
    entry character varying(8092),
    entry_date timestamp with time zone NOT NULL
);


ALTER TABLE public.inventory_system_log_entry OWNER TO conary;

--
-- Name: inventory_system_log_entry_system_log_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_log_entry_system_log_entry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_log_entry_system_log_entry_id_seq OWNER TO conary;

--
-- Name: inventory_system_log_entry_system_log_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_log_entry_system_log_entry_id_seq OWNED BY inventory_system_log_entry.system_log_entry_id;


--
-- Name: inventory_system_log_entry_system_log_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_log_entry_system_log_entry_id_seq', 1, false);


--
-- Name: inventory_system_log_system_log_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_log_system_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_log_system_log_id_seq OWNER TO conary;

--
-- Name: inventory_system_log_system_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_log_system_log_id_seq OWNED BY inventory_system_log.system_log_id;


--
-- Name: inventory_system_log_system_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_log_system_log_id_seq', 1, false);


--
-- Name: inventory_system_network; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_network (
    network_id integer NOT NULL,
    system_id integer NOT NULL,
    created_date timestamp with time zone NOT NULL,
    ip_address character varying(15),
    ipv6_address text,
    device_name character varying(255),
    dns_name character varying(255) NOT NULL,
    netmask character varying(20),
    port_type character varying(32),
    active boolean,
    required boolean
);


ALTER TABLE public.inventory_system_network OWNER TO conary;

--
-- Name: inventory_system_network_network_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_network_network_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_network_network_id_seq OWNER TO conary;

--
-- Name: inventory_system_network_network_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_network_network_id_seq OWNED BY inventory_system_network.network_id;


--
-- Name: inventory_system_network_network_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_network_network_id_seq', 1, false);


--
-- Name: inventory_system_state; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_state (
    system_state_id integer NOT NULL,
    name character varying(8092) NOT NULL,
    description character varying(8092) NOT NULL,
    created_date timestamp with time zone NOT NULL
);


ALTER TABLE public.inventory_system_state OWNER TO conary;

--
-- Name: inventory_system_state_system_state_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_state_system_state_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_state_system_state_id_seq OWNER TO conary;

--
-- Name: inventory_system_state_system_state_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_state_system_state_id_seq OWNED BY inventory_system_state.system_state_id;


--
-- Name: inventory_system_state_system_state_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_state_system_state_id_seq', 12, true);


--
-- Name: inventory_system_system_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_system_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_system_id_seq OWNER TO conary;

--
-- Name: inventory_system_system_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_system_id_seq OWNED BY inventory_system.system_id;


--
-- Name: inventory_system_system_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_system_id_seq', 1, false);


--
-- Name: inventory_system_target_credentials; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_target_credentials (
    id integer NOT NULL,
    system_id integer NOT NULL,
    credentials_id integer NOT NULL
);


ALTER TABLE public.inventory_system_target_credentials OWNER TO conary;

--
-- Name: inventory_system_target_credentials_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_target_credentials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_target_credentials_id_seq OWNER TO conary;

--
-- Name: inventory_system_target_credentials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_target_credentials_id_seq OWNED BY inventory_system_target_credentials.id;


--
-- Name: inventory_system_target_credentials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_target_credentials_id_seq', 1, false);


--
-- Name: inventory_system_type; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_system_type (
    system_type_id integer NOT NULL,
    name character varying(8092) NOT NULL,
    description character varying(8092) NOT NULL,
    created_date timestamp with time zone NOT NULL,
    infrastructure boolean NOT NULL,
    creation_descriptor text NOT NULL
);


ALTER TABLE public.inventory_system_type OWNER TO conary;

--
-- Name: inventory_system_type_system_type_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_system_type_system_type_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_system_type_system_type_id_seq OWNER TO conary;

--
-- Name: inventory_system_type_system_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_system_type_system_type_id_seq OWNED BY inventory_system_type.system_type_id;


--
-- Name: inventory_system_type_system_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_system_type_system_type_id_seq', 3, true);


--
-- Name: inventory_trove; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_trove (
    trove_id integer NOT NULL,
    name text NOT NULL,
    version_id integer NOT NULL,
    flavor text NOT NULL,
    is_top_level boolean NOT NULL,
    last_available_update_refresh timestamp with time zone,
    out_of_date boolean
);


ALTER TABLE public.inventory_trove OWNER TO conary;

--
-- Name: inventory_trove_available_updates; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_trove_available_updates (
    id integer NOT NULL,
    trove_id integer NOT NULL,
    version_id integer NOT NULL
);


ALTER TABLE public.inventory_trove_available_updates OWNER TO conary;

--
-- Name: inventory_trove_available_updates_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_trove_available_updates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_trove_available_updates_id_seq OWNER TO conary;

--
-- Name: inventory_trove_available_updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_trove_available_updates_id_seq OWNED BY inventory_trove_available_updates.id;


--
-- Name: inventory_trove_available_updates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_trove_available_updates_id_seq', 1, false);


--
-- Name: inventory_trove_trove_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_trove_trove_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_trove_trove_id_seq OWNER TO conary;

--
-- Name: inventory_trove_trove_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_trove_trove_id_seq OWNED BY inventory_trove.trove_id;


--
-- Name: inventory_trove_trove_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_trove_trove_id_seq', 1, false);


--
-- Name: inventory_version; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_version (
    version_id integer NOT NULL,
    "full" text NOT NULL,
    label text NOT NULL,
    revision text NOT NULL,
    ordering text NOT NULL,
    flavor text NOT NULL
);


ALTER TABLE public.inventory_version OWNER TO conary;

--
-- Name: inventory_version_version_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_version_version_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_version_version_id_seq OWNER TO conary;

--
-- Name: inventory_version_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_version_version_id_seq OWNED BY inventory_version.version_id;


--
-- Name: inventory_version_version_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_version_version_id_seq', 1, false);


--
-- Name: inventory_zone; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_zone (
    zone_id integer NOT NULL,
    name character varying(8092) NOT NULL,
    description character varying(8092),
    created_date timestamp with time zone NOT NULL
);


ALTER TABLE public.inventory_zone OWNER TO conary;

--
-- Name: inventory_zone_management_node; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE inventory_zone_management_node (
    system_ptr_id integer NOT NULL,
    local boolean,
    zone_id integer NOT NULL,
    node_jid character varying(64)
);


ALTER TABLE public.inventory_zone_management_node OWNER TO conary;

--
-- Name: inventory_zone_zone_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE inventory_zone_zone_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.inventory_zone_zone_id_seq OWNER TO conary;

--
-- Name: inventory_zone_zone_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE inventory_zone_zone_id_seq OWNED BY inventory_zone.zone_id;


--
-- Name: inventory_zone_zone_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('inventory_zone_zone_id_seq', 1, true);


--
-- Name: job_history; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE job_history (
    job_history_id integer NOT NULL,
    job_id integer NOT NULL,
    "timestamp" numeric(14,3) NOT NULL,
    content character varying NOT NULL
);


ALTER TABLE public.job_history OWNER TO conary;

--
-- Name: job_history_job_history_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE job_history_job_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.job_history_job_history_id_seq OWNER TO conary;

--
-- Name: job_history_job_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE job_history_job_history_id_seq OWNED BY job_history.job_history_id;


--
-- Name: job_history_job_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('job_history_job_history_id_seq', 1, false);


--
-- Name: job_results; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE job_results (
    job_result_id integer NOT NULL,
    job_id integer NOT NULL,
    data character varying NOT NULL
);


ALTER TABLE public.job_results OWNER TO conary;

--
-- Name: job_results_job_result_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE job_results_job_result_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.job_results_job_result_id_seq OWNER TO conary;

--
-- Name: job_results_job_result_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE job_results_job_result_id_seq OWNED BY job_results.job_result_id;


--
-- Name: job_results_job_result_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('job_results_job_result_id_seq', 1, false);


--
-- Name: job_states; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE job_states (
    job_state_id integer NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.job_states OWNER TO conary;

--
-- Name: job_states_job_state_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE job_states_job_state_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.job_states_job_state_id_seq OWNER TO conary;

--
-- Name: job_states_job_state_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE job_states_job_state_id_seq OWNED BY job_states.job_state_id;


--
-- Name: job_states_job_state_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('job_states_job_state_id_seq', 4, true);


--
-- Name: job_system; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE job_system (
    job_id integer NOT NULL,
    system_id integer NOT NULL
);


ALTER TABLE public.job_system OWNER TO conary;

--
-- Name: job_target; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE job_target (
    job_id integer NOT NULL,
    targetid integer NOT NULL
);


ALTER TABLE public.job_target OWNER TO conary;

--
-- Name: job_types; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE job_types (
    job_type_id integer NOT NULL,
    name character varying NOT NULL,
    description character varying NOT NULL
);


ALTER TABLE public.job_types OWNER TO conary;

--
-- Name: job_types_job_type_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE job_types_job_type_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.job_types_job_type_id_seq OWNER TO conary;

--
-- Name: job_types_job_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE job_types_job_type_id_seq OWNED BY job_types.job_type_id;


--
-- Name: job_types_job_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('job_types_job_type_id_seq', 4, true);


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE jobs (
    job_id integer NOT NULL,
    job_type_id integer NOT NULL,
    job_state_id integer NOT NULL,
    job_uuid character varying(64) NOT NULL,
    created_by integer NOT NULL,
    created numeric(14,4) NOT NULL,
    modified numeric(14,4) NOT NULL,
    expiration numeric(14,4),
    ttl integer,
    pid integer,
    message character varying,
    error_response character varying,
    rest_uri character varying,
    rest_method_id integer,
    rest_args character varying
);


ALTER TABLE public.jobs OWNER TO conary;

--
-- Name: jobs_job_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE jobs_job_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.jobs_job_id_seq OWNER TO conary;

--
-- Name: jobs_job_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE jobs_job_id_seq OWNED BY jobs.job_id;


--
-- Name: jobs_job_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('jobs_job_id_seq', 1, false);


--
-- Name: labels; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE labels (
    labelid integer NOT NULL,
    projectid integer NOT NULL,
    label character varying(255) NOT NULL,
    url character varying(255) NOT NULL,
    authtype character varying(32) DEFAULT 'none'::character varying NOT NULL,
    username character varying(255),
    password character varying(255),
    entitlement character varying(254)
);


ALTER TABLE public.labels OWNER TO conary;

--
-- Name: labels_labelid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE labels_labelid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.labels_labelid_seq OWNER TO conary;

--
-- Name: labels_labelid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE labels_labelid_seq OWNED BY labels.labelid;


--
-- Name: labels_labelid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('labels_labelid_seq', 1, false);


--
-- Name: latestcommit; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE latestcommit (
    projectid integer NOT NULL,
    committime numeric(14,3) NOT NULL
);


ALTER TABLE public.latestcommit OWNER TO conary;

--
-- Name: membershiprequests; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE membershiprequests (
    projectid integer NOT NULL,
    userid integer NOT NULL,
    comments text
);


ALTER TABLE public.membershiprequests OWNER TO conary;

--
-- Name: newscache; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE newscache (
    itemid integer NOT NULL,
    title character varying(255),
    pubdate numeric(14,3),
    content text,
    link character varying(255),
    category character varying(255)
);


ALTER TABLE public.newscache OWNER TO conary;

--
-- Name: newscache_itemid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE newscache_itemid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.newscache_itemid_seq OWNER TO conary;

--
-- Name: newscache_itemid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE newscache_itemid_seq OWNED BY newscache.itemid;


--
-- Name: newscache_itemid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('newscache_itemid_seq', 1, false);


--
-- Name: newscacheinfo; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE newscacheinfo (
    age numeric(14,3),
    feedlink character varying(255)
);


ALTER TABLE public.newscacheinfo OWNER TO conary;

--
-- Name: outboundmirrors; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE outboundmirrors (
    outboundmirrorid integer NOT NULL,
    sourceprojectid integer NOT NULL,
    targetlabels character varying(767) NOT NULL,
    alllabels smallint DEFAULT 0 NOT NULL,
    recurse smallint DEFAULT 0 NOT NULL,
    matchstrings character varying(767) DEFAULT ''::character varying NOT NULL,
    mirrororder integer DEFAULT 0,
    fullsync smallint DEFAULT 0 NOT NULL,
    usereleases integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.outboundmirrors OWNER TO conary;

--
-- Name: outboundmirrors_outboundmirrorid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE outboundmirrors_outboundmirrorid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.outboundmirrors_outboundmirrorid_seq OWNER TO conary;

--
-- Name: outboundmirrors_outboundmirrorid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE outboundmirrors_outboundmirrorid_seq OWNED BY outboundmirrors.outboundmirrorid;


--
-- Name: outboundmirrors_outboundmirrorid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('outboundmirrors_outboundmirrorid_seq', 1, false);


--
-- Name: outboundmirrorsupdateservices; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE outboundmirrorsupdateservices (
    outboundmirrorid integer NOT NULL,
    updateserviceid integer NOT NULL
);


ALTER TABLE public.outboundmirrorsupdateservices OWNER TO conary;

--
-- Name: packageindex; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE packageindex (
    pkgid integer NOT NULL,
    projectid integer NOT NULL,
    name character varying(255) NOT NULL,
    version character varying(255) NOT NULL,
    servername character varying(254) NOT NULL,
    branchname character varying(254) NOT NULL,
    issource integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.packageindex OWNER TO conary;

--
-- Name: packageindex_pkgid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE packageindex_pkgid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.packageindex_pkgid_seq OWNER TO conary;

--
-- Name: packageindex_pkgid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE packageindex_pkgid_seq OWNED BY packageindex.pkgid;


--
-- Name: packageindex_pkgid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('packageindex_pkgid_seq', 1, false);


--
-- Name: packageindexmark; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE packageindexmark (
    mark integer NOT NULL
);


ALTER TABLE public.packageindexmark OWNER TO conary;

--
-- Name: pki_certificates; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE pki_certificates (
    fingerprint text NOT NULL,
    purpose text NOT NULL,
    is_ca boolean DEFAULT false NOT NULL,
    x509_pem text NOT NULL,
    pkey_pem text NOT NULL,
    issuer_fingerprint text,
    ca_serial_index integer,
    time_issued timestamp with time zone NOT NULL,
    time_expired timestamp with time zone NOT NULL
);


ALTER TABLE public.pki_certificates OWNER TO conary;

--
-- Name: platforms; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE platforms (
    platformid integer NOT NULL,
    label character varying(255) NOT NULL,
    mode character varying(255) DEFAULT 'manual'::character varying NOT NULL,
    enabled smallint DEFAULT 1 NOT NULL,
    projectid smallint,
    platformname character varying(1024) NOT NULL,
    configurable boolean DEFAULT false NOT NULL,
    abstract boolean DEFAULT false NOT NULL,
    isfromdisk boolean DEFAULT false NOT NULL,
    time_refreshed timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT platforms_mode_check CHECK (((mode)::text = ANY ((ARRAY['auto'::character varying, 'manual'::character varying])::text[])))
);


ALTER TABLE public.platforms OWNER TO conary;

--
-- Name: platforms_platformid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE platforms_platformid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.platforms_platformid_seq OWNER TO conary;

--
-- Name: platforms_platformid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE platforms_platformid_seq OWNED BY platforms.platformid;


--
-- Name: platforms_platformid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('platforms_platformid_seq', 1, false);


--
-- Name: platformscontentsourcetypes; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE platformscontentsourcetypes (
    platformid integer NOT NULL,
    contentsourcetype character varying(255) NOT NULL
);


ALTER TABLE public.platformscontentsourcetypes OWNER TO conary;

--
-- Name: platformsourcedata; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE platformsourcedata (
    platformsourceid integer NOT NULL,
    name character varying(32) NOT NULL,
    value text NOT NULL,
    datatype smallint NOT NULL
);


ALTER TABLE public.platformsourcedata OWNER TO conary;

--
-- Name: platformsources; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE platformsources (
    platformsourceid integer NOT NULL,
    name character varying(255) NOT NULL,
    shortname character varying(255) NOT NULL,
    defaultsource smallint DEFAULT 0 NOT NULL,
    contentsourcetype character varying(255) NOT NULL,
    orderindex smallint NOT NULL
);


ALTER TABLE public.platformsources OWNER TO conary;

--
-- Name: platformsources_platformsourceid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE platformsources_platformsourceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.platformsources_platformsourceid_seq OWNER TO conary;

--
-- Name: platformsources_platformsourceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE platformsources_platformsourceid_seq OWNED BY platformsources.platformsourceid;


--
-- Name: platformsources_platformsourceid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('platformsources_platformsourceid_seq', 1, false);


--
-- Name: platformsplatformsources; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE platformsplatformsources (
    platformid integer NOT NULL,
    platformsourceid integer NOT NULL
);


ALTER TABLE public.platformsplatformsources OWNER TO conary;

--
-- Name: popularprojects; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE popularprojects (
    projectid integer NOT NULL,
    rank integer NOT NULL
);


ALTER TABLE public.popularprojects OWNER TO conary;

--
-- Name: productversions; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE productversions (
    productversionid integer NOT NULL,
    projectid integer NOT NULL,
    namespace character varying(16) NOT NULL,
    name character varying(16) NOT NULL,
    description text,
    timecreated numeric(14,3)
);


ALTER TABLE public.productversions OWNER TO conary;

--
-- Name: productversions_productversionid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE productversions_productversionid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.productversions_productversionid_seq OWNER TO conary;

--
-- Name: productversions_productversionid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE productversions_productversionid_seq OWNED BY productversions.productversionid;


--
-- Name: productversions_productversionid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('productversions_productversionid_seq', 1, false);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE projects (
    projectid integer NOT NULL,
    creatorid integer,
    name character varying(128) NOT NULL,
    hostname character varying(63) NOT NULL,
    shortname character varying(63) NOT NULL,
    domainname character varying(128) DEFAULT ''::character varying NOT NULL,
    fqdn character varying(255) NOT NULL,
    namespace character varying(16),
    projecturl character varying(128) DEFAULT ''::character varying NOT NULL,
    description text,
    disabled smallint DEFAULT 0 NOT NULL,
    hidden smallint DEFAULT 0 NOT NULL,
    external smallint DEFAULT 0 NOT NULL,
    isappliance smallint DEFAULT 1 NOT NULL,
    timecreated numeric(14,3),
    timemodified numeric(14,3),
    commitemail character varying(128) DEFAULT ''::character varying,
    prodtype character varying(128) DEFAULT ''::character varying,
    version character varying(128) DEFAULT ''::character varying,
    backupexternal smallint DEFAULT 0 NOT NULL,
    database character varying(128)
);


ALTER TABLE public.projects OWNER TO conary;

--
-- Name: projects_projectid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE projects_projectid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.projects_projectid_seq OWNER TO conary;

--
-- Name: projects_projectid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE projects_projectid_seq OWNED BY projects.projectid;


--
-- Name: projects_projectid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('projects_projectid_seq', 1, false);


--
-- Name: projectusers; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE projectusers (
    projectid integer NOT NULL,
    userid integer NOT NULL,
    level smallint NOT NULL
);


ALTER TABLE public.projectusers OWNER TO conary;

--
-- Name: publishedreleases; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE publishedreleases (
    pubreleaseid integer NOT NULL,
    projectid integer NOT NULL,
    name character varying(255) DEFAULT ''::character varying NOT NULL,
    version character varying(32) DEFAULT ''::character varying NOT NULL,
    description text,
    timecreated numeric(14,3),
    createdby integer,
    timeupdated numeric(14,3),
    updatedby integer,
    timepublished numeric(14,3),
    publishedby integer,
    shouldmirror smallint DEFAULT 0 NOT NULL,
    timemirrored numeric(14,3)
);


ALTER TABLE public.publishedreleases OWNER TO conary;

--
-- Name: publishedreleases_pubreleaseid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE publishedreleases_pubreleaseid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.publishedreleases_pubreleaseid_seq OWNER TO conary;

--
-- Name: publishedreleases_pubreleaseid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE publishedreleases_pubreleaseid_seq OWNED BY publishedreleases.pubreleaseid;


--
-- Name: publishedreleases_pubreleaseid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('publishedreleases_pubreleaseid_seq', 1, false);


--
-- Name: querysets_filterentry; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE querysets_filterentry (
    filter_entry_id integer NOT NULL,
    field text NOT NULL,
    operator text NOT NULL,
    value text
);


ALTER TABLE public.querysets_filterentry OWNER TO conary;

--
-- Name: querysets_filterentry_filter_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE querysets_filterentry_filter_entry_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.querysets_filterentry_filter_entry_id_seq OWNER TO conary;

--
-- Name: querysets_filterentry_filter_entry_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE querysets_filterentry_filter_entry_id_seq OWNED BY querysets_filterentry.filter_entry_id;


--
-- Name: querysets_filterentry_filter_entry_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('querysets_filterentry_filter_entry_id_seq', 3, true);


--
-- Name: querysets_inclusionmethod; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE querysets_inclusionmethod (
    inclusion_method_id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.querysets_inclusionmethod OWNER TO conary;

--
-- Name: querysets_inclusionmethod_inclusion_method_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE querysets_inclusionmethod_inclusion_method_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.querysets_inclusionmethod_inclusion_method_id_seq OWNER TO conary;

--
-- Name: querysets_inclusionmethod_inclusion_method_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE querysets_inclusionmethod_inclusion_method_id_seq OWNED BY querysets_inclusionmethod.inclusion_method_id;


--
-- Name: querysets_inclusionmethod_inclusion_method_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('querysets_inclusionmethod_inclusion_method_id_seq', 2, true);


--
-- Name: querysets_queryset; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE querysets_queryset (
    query_set_id integer NOT NULL,
    name text NOT NULL,
    description text,
    created_date timestamp with time zone NOT NULL,
    modified_date timestamp with time zone NOT NULL,
    resource_type text NOT NULL,
    can_modify boolean DEFAULT true NOT NULL
);


ALTER TABLE public.querysets_queryset OWNER TO conary;

--
-- Name: querysets_queryset_children; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE querysets_queryset_children (
    id integer NOT NULL,
    from_queryset_id integer NOT NULL,
    to_queryset_id integer NOT NULL
);


ALTER TABLE public.querysets_queryset_children OWNER TO conary;

--
-- Name: querysets_queryset_children_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE querysets_queryset_children_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.querysets_queryset_children_id_seq OWNER TO conary;

--
-- Name: querysets_queryset_children_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE querysets_queryset_children_id_seq OWNED BY querysets_queryset_children.id;


--
-- Name: querysets_queryset_children_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('querysets_queryset_children_id_seq', 2, true);


--
-- Name: querysets_queryset_filter_entries; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE querysets_queryset_filter_entries (
    id integer NOT NULL,
    queryset_id integer NOT NULL,
    filterentry_id integer NOT NULL
);


ALTER TABLE public.querysets_queryset_filter_entries OWNER TO conary;

--
-- Name: querysets_queryset_filter_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE querysets_queryset_filter_entries_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.querysets_queryset_filter_entries_id_seq OWNER TO conary;

--
-- Name: querysets_queryset_filter_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE querysets_queryset_filter_entries_id_seq OWNED BY querysets_queryset_filter_entries.id;


--
-- Name: querysets_queryset_filter_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('querysets_queryset_filter_entries_id_seq', 3, true);


--
-- Name: querysets_queryset_query_set_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE querysets_queryset_query_set_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.querysets_queryset_query_set_id_seq OWNER TO conary;

--
-- Name: querysets_queryset_query_set_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE querysets_queryset_query_set_id_seq OWNED BY querysets_queryset.query_set_id;


--
-- Name: querysets_queryset_query_set_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('querysets_queryset_query_set_id_seq', 4, true);


--
-- Name: querysets_querytag; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE querysets_querytag (
    query_tag_id integer NOT NULL,
    query_set_id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.querysets_querytag OWNER TO conary;

--
-- Name: querysets_querytag_query_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE querysets_querytag_query_tag_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.querysets_querytag_query_tag_id_seq OWNER TO conary;

--
-- Name: querysets_querytag_query_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE querysets_querytag_query_tag_id_seq OWNED BY querysets_querytag.query_tag_id;


--
-- Name: querysets_querytag_query_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('querysets_querytag_query_tag_id_seq', 4, true);


--
-- Name: querysets_systemtag; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE querysets_systemtag (
    system_tag_id integer NOT NULL,
    system_id integer NOT NULL,
    query_tag_id integer NOT NULL,
    inclusion_method_id integer NOT NULL
);


ALTER TABLE public.querysets_systemtag OWNER TO conary;

--
-- Name: querysets_systemtag_system_tag_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE querysets_systemtag_system_tag_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.querysets_systemtag_system_tag_id_seq OWNER TO conary;

--
-- Name: querysets_systemtag_system_tag_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE querysets_systemtag_system_tag_id_seq OWNED BY querysets_systemtag.system_tag_id;


--
-- Name: querysets_systemtag_system_tag_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('querysets_systemtag_system_tag_id_seq', 1, false);


--
-- Name: repnamemap; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE repnamemap (
    fromname character varying(254) NOT NULL,
    toname character varying(254) NOT NULL
);


ALTER TABLE public.repnamemap OWNER TO conary;

--
-- Name: repositorylogstatus; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE repositorylogstatus (
    logname character varying(128) NOT NULL,
    inode integer NOT NULL,
    logoffset integer NOT NULL
);


ALTER TABLE public.repositorylogstatus OWNER TO conary;

--
-- Name: rest_methods; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE rest_methods (
    rest_method_id integer NOT NULL,
    name character varying NOT NULL
);


ALTER TABLE public.rest_methods OWNER TO conary;

--
-- Name: rest_methods_rest_method_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE rest_methods_rest_method_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.rest_methods_rest_method_id_seq OWNER TO conary;

--
-- Name: rest_methods_rest_method_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE rest_methods_rest_method_id_seq OWNED BY rest_methods.rest_method_id;


--
-- Name: rest_methods_rest_method_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('rest_methods_rest_method_id_seq', 3, true);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE sessions (
    sessidx integer NOT NULL,
    sid character varying(64) NOT NULL,
    data text
);


ALTER TABLE public.sessions OWNER TO conary;

--
-- Name: sessions_sessidx_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE sessions_sessidx_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.sessions_sessidx_seq OWNER TO conary;

--
-- Name: sessions_sessidx_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE sessions_sessidx_seq OWNED BY sessions.sessidx;


--
-- Name: sessions_sessidx_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('sessions_sessidx_seq', 1, false);


--
-- Name: systemupdate; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE systemupdate (
    systemupdateid integer NOT NULL,
    servername character varying(128) NOT NULL,
    repositoryname character varying(128) NOT NULL,
    updatetime numeric(14,3) NOT NULL,
    updateuser character varying(128) NOT NULL
);


ALTER TABLE public.systemupdate OWNER TO conary;

--
-- Name: systemupdate_systemupdateid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE systemupdate_systemupdateid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.systemupdate_systemupdateid_seq OWNER TO conary;

--
-- Name: systemupdate_systemupdateid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE systemupdate_systemupdateid_seq OWNED BY systemupdate.systemupdateid;


--
-- Name: systemupdate_systemupdateid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('systemupdate_systemupdateid_seq', 1, false);


--
-- Name: targetcredentials; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE targetcredentials (
    targetcredentialsid integer NOT NULL,
    credentials text NOT NULL
);


ALTER TABLE public.targetcredentials OWNER TO conary;

--
-- Name: targetcredentials_targetcredentialsid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE targetcredentials_targetcredentialsid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.targetcredentials_targetcredentialsid_seq OWNER TO conary;

--
-- Name: targetcredentials_targetcredentialsid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE targetcredentials_targetcredentialsid_seq OWNED BY targetcredentials.targetcredentialsid;


--
-- Name: targetcredentials_targetcredentialsid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('targetcredentials_targetcredentialsid_seq', 1, false);


--
-- Name: targetdata; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE targetdata (
    targetid integer NOT NULL,
    name character varying(255) NOT NULL,
    value text
);


ALTER TABLE public.targetdata OWNER TO conary;

--
-- Name: targetimagesdeployed; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE targetimagesdeployed (
    id integer NOT NULL,
    targetid integer NOT NULL,
    fileid integer NOT NULL,
    targetimageid character varying(128) NOT NULL
);


ALTER TABLE public.targetimagesdeployed OWNER TO conary;

--
-- Name: targetimagesdeployed_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE targetimagesdeployed_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.targetimagesdeployed_id_seq OWNER TO conary;

--
-- Name: targetimagesdeployed_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE targetimagesdeployed_id_seq OWNED BY targetimagesdeployed.id;


--
-- Name: targetimagesdeployed_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('targetimagesdeployed_id_seq', 1, false);


--
-- Name: targets; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE targets (
    targetid integer NOT NULL,
    targettype character varying(255) NOT NULL,
    targetname character varying(255) NOT NULL
);


ALTER TABLE public.targets OWNER TO conary;

--
-- Name: targets_targetid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE targets_targetid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.targets_targetid_seq OWNER TO conary;

--
-- Name: targets_targetid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE targets_targetid_seq OWNED BY targets.targetid;


--
-- Name: targets_targetid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('targets_targetid_seq', 1, false);


--
-- Name: targetusercredentials; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE targetusercredentials (
    id integer NOT NULL,
    targetid integer NOT NULL,
    userid integer NOT NULL,
    targetcredentialsid integer NOT NULL
);


ALTER TABLE public.targetusercredentials OWNER TO conary;

--
-- Name: targetusercredentials_id_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE targetusercredentials_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.targetusercredentials_id_seq OWNER TO conary;

--
-- Name: targetusercredentials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE targetusercredentials_id_seq OWNED BY targetusercredentials.id;


--
-- Name: targetusercredentials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('targetusercredentials_id_seq', 1, false);


--
-- Name: topprojects; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE topprojects (
    projectid integer NOT NULL,
    rank integer NOT NULL
);


ALTER TABLE public.topprojects OWNER TO conary;

--
-- Name: updateservices; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE updateservices (
    updateserviceid integer NOT NULL,
    hostname character varying(767) NOT NULL,
    description text,
    mirroruser character varying(254) NOT NULL,
    mirrorpassword character varying(254) NOT NULL
);


ALTER TABLE public.updateservices OWNER TO conary;

--
-- Name: updateservices_updateserviceid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE updateservices_updateserviceid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.updateservices_updateserviceid_seq OWNER TO conary;

--
-- Name: updateservices_updateserviceid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE updateservices_updateserviceid_seq OWNED BY updateservices.updateserviceid;


--
-- Name: updateservices_updateserviceid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('updateservices_updateserviceid_seq', 1, false);


--
-- Name: urldownloads; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE urldownloads (
    urlid integer NOT NULL,
    timedownloaded numeric(14,0) DEFAULT 0 NOT NULL,
    ip character varying(64) NOT NULL
);


ALTER TABLE public.urldownloads OWNER TO conary;

--
-- Name: useit; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE useit (
    itemid integer NOT NULL,
    name character varying(255),
    link character varying(255)
);


ALTER TABLE public.useit OWNER TO conary;

--
-- Name: useit_itemid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE useit_itemid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.useit_itemid_seq OWNER TO conary;

--
-- Name: useit_itemid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE useit_itemid_seq OWNED BY useit.itemid;


--
-- Name: useit_itemid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('useit_itemid_seq', 1, false);


--
-- Name: userdata; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE userdata (
    userid integer NOT NULL,
    name character varying(32) NOT NULL,
    value text,
    datatype integer
);


ALTER TABLE public.userdata OWNER TO conary;

--
-- Name: usergroupmembers; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE usergroupmembers (
    usergroupid integer NOT NULL,
    userid integer NOT NULL
);


ALTER TABLE public.usergroupmembers OWNER TO conary;

--
-- Name: usergroups; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE usergroups (
    usergroupid integer NOT NULL,
    usergroup character varying(128) NOT NULL
);


ALTER TABLE public.usergroups OWNER TO conary;

--
-- Name: usergroups_usergroupid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE usergroups_usergroupid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.usergroups_usergroupid_seq OWNER TO conary;

--
-- Name: usergroups_usergroupid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE usergroups_usergroupid_seq OWNED BY usergroups.usergroupid;


--
-- Name: usergroups_usergroupid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('usergroups_usergroupid_seq', 1, false);


--
-- Name: users; Type: TABLE; Schema: public; Owner: conary; Tablespace: 
--

CREATE TABLE users (
    userid integer NOT NULL,
    username character varying(128) NOT NULL,
    fullname character varying(128) DEFAULT ''::character varying NOT NULL,
    salt bytea,
    passwd character varying(254),
    email character varying(128),
    displayemail text,
    timecreated numeric(14,3),
    timeaccessed numeric(14,3),
    active smallint,
    blurb text
);


ALTER TABLE public.users OWNER TO conary;

--
-- Name: users_userid_seq; Type: SEQUENCE; Schema: public; Owner: conary
--

CREATE SEQUENCE users_userid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.users_userid_seq OWNER TO conary;

--
-- Name: users_userid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: conary
--

ALTER SEQUENCE users_userid_seq OWNED BY users.userid;


--
-- Name: users_userid_seq; Type: SEQUENCE SET; Schema: public; Owner: conary
--

SELECT pg_catalog.setval('users_userid_seq', 1, false);


--
-- Name: itemid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE appliancespotlight ALTER COLUMN itemid SET DEFAULT nextval('appliancespotlight_itemid_seq'::regclass);


--
-- Name: fileid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE buildfiles ALTER COLUMN fileid SET DEFAULT nextval('buildfiles_fileid_seq'::regclass);


--
-- Name: buildid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE builds ALTER COLUMN buildid SET DEFAULT nextval('builds_buildid_seq'::regclass);


--
-- Name: change_log_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE changelog_change_log ALTER COLUMN change_log_id SET DEFAULT nextval('changelog_change_log_change_log_id_seq'::regclass);


--
-- Name: change_log_entry_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE changelog_change_log_entry ALTER COLUMN change_log_entry_id SET DEFAULT nextval('changelog_change_log_entry_change_log_entry_id_seq'::regclass);


--
-- Name: channel_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE ci_rhn_channels ALTER COLUMN channel_id SET DEFAULT nextval('ci_rhn_channels_channel_id_seq'::regclass);


--
-- Name: errata_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE ci_rhn_errata ALTER COLUMN errata_id SET DEFAULT nextval('ci_rhn_errata_errata_id_seq'::regclass);


--
-- Name: nevra_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE ci_rhn_nevra ALTER COLUMN nevra_id SET DEFAULT nextval('ci_rhn_nevra_nevra_id_seq'::regclass);


--
-- Name: package_failed_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE ci_rhn_package_failed ALTER COLUMN package_failed_id SET DEFAULT nextval('ci_rhn_package_failed_package_failed_id_seq'::regclass);


--
-- Name: package_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE ci_rhn_packages ALTER COLUMN package_id SET DEFAULT nextval('ci_rhn_packages_package_id_seq'::regclass);


--
-- Name: package_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE ci_yum_packages ALTER COLUMN package_id SET DEFAULT nextval('ci_yum_packages_package_id_seq'::regclass);


--
-- Name: yum_repository_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE ci_yum_repositories ALTER COLUMN yum_repository_id SET DEFAULT nextval('ci_yum_repositories_yum_repository_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE django_redirect ALTER COLUMN id SET DEFAULT nextval('django_redirect_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE django_site ALTER COLUMN id SET DEFAULT nextval('django_site_id_seq'::regclass);


--
-- Name: urlid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE filesurls ALTER COLUMN urlid SET DEFAULT nextval('filesurls_urlid_seq'::regclass);


--
-- Name: itemid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE frontpageselections ALTER COLUMN itemid SET DEFAULT nextval('frontpageselections_itemid_seq'::regclass);


--
-- Name: inboundmirrorid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inboundmirrors ALTER COLUMN inboundmirrorid SET DEFAULT nextval('inboundmirrors_inboundmirrorid_seq'::regclass);


--
-- Name: event_type_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_event_type ALTER COLUMN event_type_id SET DEFAULT nextval('inventory_event_type_event_type_id_seq'::regclass);


--
-- Name: job_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_job ALTER COLUMN job_id SET DEFAULT nextval('inventory_job_job_id_seq'::regclass);


--
-- Name: job_state_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_job_state ALTER COLUMN job_state_id SET DEFAULT nextval('inventory_job_state_job_state_id_seq'::regclass);


--
-- Name: management_interface_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_management_interface ALTER COLUMN management_interface_id SET DEFAULT nextval('inventory_management_interface_management_interface_id_seq'::regclass);


--
-- Name: stage_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_stage ALTER COLUMN stage_id SET DEFAULT nextval('inventory_stage_stage_id_seq'::regclass);


--
-- Name: system_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system ALTER COLUMN system_id SET DEFAULT nextval('inventory_system_system_id_seq'::regclass);


--
-- Name: system_event_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_event ALTER COLUMN system_event_id SET DEFAULT nextval('inventory_system_event_system_event_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_installed_software ALTER COLUMN id SET DEFAULT nextval('inventory_system_installed_software_id_seq'::regclass);


--
-- Name: system_job_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_job ALTER COLUMN system_job_id SET DEFAULT nextval('inventory_system_job_system_job_id_seq'::regclass);


--
-- Name: system_log_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_log ALTER COLUMN system_log_id SET DEFAULT nextval('inventory_system_log_system_log_id_seq'::regclass);


--
-- Name: system_log_entry_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_log_entry ALTER COLUMN system_log_entry_id SET DEFAULT nextval('inventory_system_log_entry_system_log_entry_id_seq'::regclass);


--
-- Name: network_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_network ALTER COLUMN network_id SET DEFAULT nextval('inventory_system_network_network_id_seq'::regclass);


--
-- Name: system_state_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_state ALTER COLUMN system_state_id SET DEFAULT nextval('inventory_system_state_system_state_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_target_credentials ALTER COLUMN id SET DEFAULT nextval('inventory_system_target_credentials_id_seq'::regclass);


--
-- Name: system_type_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_system_type ALTER COLUMN system_type_id SET DEFAULT nextval('inventory_system_type_system_type_id_seq'::regclass);


--
-- Name: trove_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_trove ALTER COLUMN trove_id SET DEFAULT nextval('inventory_trove_trove_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_trove_available_updates ALTER COLUMN id SET DEFAULT nextval('inventory_trove_available_updates_id_seq'::regclass);


--
-- Name: version_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_version ALTER COLUMN version_id SET DEFAULT nextval('inventory_version_version_id_seq'::regclass);


--
-- Name: zone_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE inventory_zone ALTER COLUMN zone_id SET DEFAULT nextval('inventory_zone_zone_id_seq'::regclass);


--
-- Name: job_history_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE job_history ALTER COLUMN job_history_id SET DEFAULT nextval('job_history_job_history_id_seq'::regclass);


--
-- Name: job_result_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE job_results ALTER COLUMN job_result_id SET DEFAULT nextval('job_results_job_result_id_seq'::regclass);


--
-- Name: job_state_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE job_states ALTER COLUMN job_state_id SET DEFAULT nextval('job_states_job_state_id_seq'::regclass);


--
-- Name: job_type_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE job_types ALTER COLUMN job_type_id SET DEFAULT nextval('job_types_job_type_id_seq'::regclass);


--
-- Name: job_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE jobs ALTER COLUMN job_id SET DEFAULT nextval('jobs_job_id_seq'::regclass);


--
-- Name: labelid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE labels ALTER COLUMN labelid SET DEFAULT nextval('labels_labelid_seq'::regclass);


--
-- Name: itemid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE newscache ALTER COLUMN itemid SET DEFAULT nextval('newscache_itemid_seq'::regclass);


--
-- Name: outboundmirrorid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE outboundmirrors ALTER COLUMN outboundmirrorid SET DEFAULT nextval('outboundmirrors_outboundmirrorid_seq'::regclass);


--
-- Name: pkgid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE packageindex ALTER COLUMN pkgid SET DEFAULT nextval('packageindex_pkgid_seq'::regclass);


--
-- Name: platformid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE platforms ALTER COLUMN platformid SET DEFAULT nextval('platforms_platformid_seq'::regclass);


--
-- Name: platformsourceid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE platformsources ALTER COLUMN platformsourceid SET DEFAULT nextval('platformsources_platformsourceid_seq'::regclass);


--
-- Name: productversionid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE productversions ALTER COLUMN productversionid SET DEFAULT nextval('productversions_productversionid_seq'::regclass);


--
-- Name: projectid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE projects ALTER COLUMN projectid SET DEFAULT nextval('projects_projectid_seq'::regclass);


--
-- Name: pubreleaseid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE publishedreleases ALTER COLUMN pubreleaseid SET DEFAULT nextval('publishedreleases_pubreleaseid_seq'::regclass);


--
-- Name: filter_entry_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE querysets_filterentry ALTER COLUMN filter_entry_id SET DEFAULT nextval('querysets_filterentry_filter_entry_id_seq'::regclass);


--
-- Name: inclusion_method_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE querysets_inclusionmethod ALTER COLUMN inclusion_method_id SET DEFAULT nextval('querysets_inclusionmethod_inclusion_method_id_seq'::regclass);


--
-- Name: query_set_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE querysets_queryset ALTER COLUMN query_set_id SET DEFAULT nextval('querysets_queryset_query_set_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE querysets_queryset_children ALTER COLUMN id SET DEFAULT nextval('querysets_queryset_children_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE querysets_queryset_filter_entries ALTER COLUMN id SET DEFAULT nextval('querysets_queryset_filter_entries_id_seq'::regclass);


--
-- Name: query_tag_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE querysets_querytag ALTER COLUMN query_tag_id SET DEFAULT nextval('querysets_querytag_query_tag_id_seq'::regclass);


--
-- Name: system_tag_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE querysets_systemtag ALTER COLUMN system_tag_id SET DEFAULT nextval('querysets_systemtag_system_tag_id_seq'::regclass);


--
-- Name: rest_method_id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE rest_methods ALTER COLUMN rest_method_id SET DEFAULT nextval('rest_methods_rest_method_id_seq'::regclass);


--
-- Name: sessidx; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE sessions ALTER COLUMN sessidx SET DEFAULT nextval('sessions_sessidx_seq'::regclass);


--
-- Name: systemupdateid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE systemupdate ALTER COLUMN systemupdateid SET DEFAULT nextval('systemupdate_systemupdateid_seq'::regclass);


--
-- Name: targetcredentialsid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE targetcredentials ALTER COLUMN targetcredentialsid SET DEFAULT nextval('targetcredentials_targetcredentialsid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE targetimagesdeployed ALTER COLUMN id SET DEFAULT nextval('targetimagesdeployed_id_seq'::regclass);


--
-- Name: targetid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE targets ALTER COLUMN targetid SET DEFAULT nextval('targets_targetid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE targetusercredentials ALTER COLUMN id SET DEFAULT nextval('targetusercredentials_id_seq'::regclass);


--
-- Name: updateserviceid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE updateservices ALTER COLUMN updateserviceid SET DEFAULT nextval('updateservices_updateserviceid_seq'::regclass);


--
-- Name: itemid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE useit ALTER COLUMN itemid SET DEFAULT nextval('useit_itemid_seq'::regclass);


--
-- Name: usergroupid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE usergroups ALTER COLUMN usergroupid SET DEFAULT nextval('usergroups_usergroupid_seq'::regclass);


--
-- Name: userid; Type: DEFAULT; Schema: public; Owner: conary
--

ALTER TABLE users ALTER COLUMN userid SET DEFAULT nextval('users_userid_seq'::regclass);


--
-- Data for Name: appliancespotlight; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY appliancespotlight (itemid, title, text, link, logo, showarchive, startdate, enddate) FROM stdin;
\.


--
-- Data for Name: builddata; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY builddata (buildid, name, value, datatype) FROM stdin;
\.


--
-- Data for Name: buildfiles; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY buildfiles (fileid, buildid, idx, title, size, sha1) FROM stdin;
\.


--
-- Data for Name: buildfilesurlsmap; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY buildfilesurlsmap (fileid, urlid) FROM stdin;
\.


--
-- Data for Name: builds; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY builds (buildid, projectid, pubreleaseid, buildtype, job_uuid, name, description, trovename, troveversion, troveflavor, trovelastchanged, timecreated, createdby, timeupdated, updatedby, buildcount, productversionid, stagename, status, statusmessage) FROM stdin;
\.


--
-- Data for Name: changelog_change_log; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY changelog_change_log (change_log_id, resource_type, resource_id) FROM stdin;
\.


--
-- Data for Name: changelog_change_log_entry; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY changelog_change_log_entry (change_log_entry_id, change_log_id, entry_text, entry_date) FROM stdin;
\.


--
-- Data for Name: ci_rhn_channel_package; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_channel_package (channel_id, package_id) FROM stdin;
\.


--
-- Data for Name: ci_rhn_channels; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_channels (channel_id, label, last_modified) FROM stdin;
\.


--
-- Data for Name: ci_rhn_errata; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_errata (errata_id, advisory, advisory_type, issue_date, last_modified_date, synopsis, update_date) FROM stdin;
\.


--
-- Data for Name: ci_rhn_errata_channel; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_errata_channel (errata_id, channel_id) FROM stdin;
\.


--
-- Data for Name: ci_rhn_errata_nevra_channel; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_errata_nevra_channel (errata_id, nevra_id, channel_id) FROM stdin;
\.


--
-- Data for Name: ci_rhn_nevra; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_nevra (nevra_id, name, epoch, version, release, arch) FROM stdin;
\.


--
-- Data for Name: ci_rhn_package_failed; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_package_failed (package_failed_id, package_id, failed_timestamp, failed_msg, resolved) FROM stdin;
\.


--
-- Data for Name: ci_rhn_packages; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_rhn_packages (package_id, nevra_id, md5sum, sha1sum, last_modified, path) FROM stdin;
\.


--
-- Data for Name: ci_yum_packages; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_yum_packages (package_id, nevra_id, sha1sum, checksum, checksum_type, path) FROM stdin;
\.


--
-- Data for Name: ci_yum_repositories; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_yum_repositories (yum_repository_id, label, "timestamp", checksum, checksum_type) FROM stdin;
\.


--
-- Data for Name: ci_yum_repository_package; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY ci_yum_repository_package (yum_repository_id, package_id, location) FROM stdin;
\.


--
-- Data for Name: commits; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY commits (projectid, "timestamp", trovename, version, userid) FROM stdin;
\.


--
-- Data for Name: communityids; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY communityids (projectid, communitytype, communityid) FROM stdin;
\.


--
-- Data for Name: confirmations; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY confirmations (userid, timerequested, confirmation) FROM stdin;
\.


--
-- Data for Name: databaseversion; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY databaseversion (version, minor) FROM stdin;
54	0
\.


--
-- Data for Name: django_redirect; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY django_redirect (id, site_id, old_path, new_path) FROM stdin;
\.


--
-- Data for Name: django_site; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY django_site (id, domain, name) FROM stdin;
1	rbuilder.inventory	rBuilder Inventory
\.


--
-- Data for Name: filesurls; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY filesurls (urlid, urltype, url) FROM stdin;
\.


--
-- Data for Name: frontpageselections; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY frontpageselections (itemid, name, link, rank) FROM stdin;
\.


--
-- Data for Name: inboundmirrors; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inboundmirrors (inboundmirrorid, targetprojectid, sourcelabels, sourceurl, sourceauthtype, sourceusername, sourcepassword, sourceentitlement, mirrororder, alllabels) FROM stdin;
\.


--
-- Data for Name: inventory_event_type; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_event_type (event_type_id, name, description, priority) FROM stdin;
1	system registration	System registration	110
2	system poll	System synchronization	50
3	immediate system poll	On-demand system synchronization	105
4	system apply update	Scheduled system update	50
5	immediate system apply update	System update	105
6	system shutdown	Scheduled system shutdown	50
7	immediate system shutdown	System shutdown	105
8	system launch wait	Launched system network data discovery	105
9	system detect management interface	System management interface detection	50
10	immediate system detect management interface	On-demand system management interface detection	105
11	immediate system configuration	Update system configuration	105
\.


--
-- Data for Name: inventory_job; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_job (job_id, job_uuid, job_state_id, event_type_id, status_code, status_text, status_detail, time_created, time_updated) FROM stdin;
\.


--
-- Data for Name: inventory_job_state; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_job_state (job_state_id, name) FROM stdin;
1	Queued
2	Running
3	Completed
4	Failed
\.


--
-- Data for Name: inventory_management_interface; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_management_interface (management_interface_id, name, description, created_date, port, credentials_descriptor, credentials_readonly) FROM stdin;
1	cim	Common Information Model (CIM)	2011-10-05 13:38:31.708487-04	5989	<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">\n  <metadata></metadata>\n  <dataFields>\n    <field>\n      <name>ssl_client_certificate</name>\n      <descriptions>\n        <desc>Client Certificate</desc>\n      </descriptions>\n      <type>str</type>\n      <constraints>\n        <descriptions>\n          <desc>The certificate must start with '-----BEGIN CERTIFICATE-----', end with '-----END CERTIFICATE-----', and have a maximum length of 16384 characters.</desc>\n        </descriptions>\n        <regexp>^\\s*-----BEGIN CERTIFICATE-----.*-----END CERTIFICATE-----\\s*$</regexp>\n        <length>16384</length>\n      </constraints>\n      <required>true</required>\n      <allowFileContent>true</allowFileContent>\n    </field>\n    <field>\n      <name>ssl_client_key</name>\n      <descriptions>\n        <desc>Client Private Key</desc>\n      </descriptions>\n      <type>str</type>\n      <constraints>\n        <descriptions>\n          <desc>The key must start with '-----BEGIN PRIVATE KEY-----', end with '----END PRIVATE KEY-----', and have a maximum length of 16384 characters.</desc>\n        </descriptions>\n        <regexp>^\\s*-----BEGIN (\\S+ )?PRIVATE KEY-----.*-----END (\\S+ )?PRIVATE KEY-----\\s*$</regexp>\n        <length>16384</length>\n      </constraints>\n      <required>true</required>\n     <allowFileContent>true</allowFileContent>\n    </field>\n  </dataFields>\n</descriptor>	t
2	wmi	Windows Management Instrumentation (WMI)	2011-10-05 13:38:31.709985-04	135	<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd">\n  <metadata></metadata>\n  <dataFields>\n    <field><name>domain</name>\n      <descriptions>\n        <desc>Windows Domain</desc>\n      </descriptions>\n      <type>str</type>\n      <default></default>\n      <required>true</required>\n    </field>\n    <field>\n      <name>username</name>\n      <descriptions>\n        <desc>User</desc>\n      </descriptions>\n      <type>str</type>\n      <default></default>\n      <required>true</required>\n    </field>\n    <field>\n      <name>password</name>\n      <descriptions>\n        <desc>Password</desc>\n      </descriptions>\n      <password>true</password>\n      <type>str</type>\n      <default></default>\n      <required>true</required>\n    </field>\n  </dataFields>\n</descriptor>	f
\.


--
-- Data for Name: inventory_stage; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_stage (stage_id, name, label, major_version_id) FROM stdin;
\.


--
-- Data for Name: inventory_system; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system (system_id, name, description, created_date, hostname, launch_date, target_id, target_system_id, target_system_name, target_system_description, target_system_state, registration_date, generated_uuid, local_uuid, ssl_client_certificate, ssl_client_key, ssl_server_certificate, agent_port, state_change_date, launching_user_id, current_state_id, managing_zone_id, management_interface_id, system_type_id, credentials, configuration, stage_id, major_version_id, appliance_id) FROM stdin;
\.


--
-- Data for Name: inventory_system_event; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_event (system_event_id, system_id, event_type_id, time_created, time_enabled, priority, event_data) FROM stdin;
\.


--
-- Data for Name: inventory_system_installed_software; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_installed_software (id, system_id, trove_id) FROM stdin;
\.


--
-- Data for Name: inventory_system_job; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_job (system_job_id, job_id, system_id, event_uuid) FROM stdin;
\.


--
-- Data for Name: inventory_system_log; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_log (system_log_id, system_id) FROM stdin;
\.


--
-- Data for Name: inventory_system_log_entry; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_log_entry (system_log_entry_id, system_log_id, entry, entry_date) FROM stdin;
\.


--
-- Data for Name: inventory_system_network; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_network (network_id, system_id, created_date, ip_address, ipv6_address, device_name, dns_name, netmask, port_type, active, required) FROM stdin;
\.


--
-- Data for Name: inventory_system_state; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_state (system_state_id, name, description, created_date) FROM stdin;
1	unmanaged	Unmanaged	2011-10-05 13:38:31.696068-04
2	unmanaged-credentials	Unmanaged: Invalid credentials	2011-10-05 13:38:31.696111-04
3	registered	Initial synchronization pending	2011-10-05 13:38:31.696126-04
4	responsive	Online	2011-10-05 13:38:31.69614-04
5	non-responsive-unknown	Not responding: Unknown	2011-10-05 13:38:31.696154-04
6	non-responsive-net	Not responding: Network unreachable	2011-10-05 13:38:31.696168-04
7	non-responsive-host	Not responding: Host unreachable	2011-10-05 13:38:31.696181-04
8	non-responsive-shutdown	Not responding: Shutdown	2011-10-05 13:38:31.696194-04
9	non-responsive-suspended	Not responding: Suspended	2011-10-05 13:38:31.696208-04
10	non-responsive-credentials	Not responding: Invalid credentials	2011-10-05 13:38:31.69622-04
11	dead	Stale	2011-10-05 13:38:31.69624-04
12	mothballed	Retired	2011-10-05 13:38:31.696255-04
\.


--
-- Data for Name: inventory_system_target_credentials; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_target_credentials (id, system_id, credentials_id) FROM stdin;
\.


--
-- Data for Name: inventory_system_type; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_system_type (system_type_id, name, description, created_date, infrastructure, creation_descriptor) FROM stdin;
1	inventory	Inventory	2011-10-05 13:38:31.715382-04	f	<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> \n  <metadata>\n  </metadata> \n  <dataFields>\n    <field> \n      <name>name</name> \n      <help lang="en_US">@System_creation_name@</help>\n      <descriptions> \n        <desc>System Name</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>true</required>\n      <prompt>\n        <desc>Enter the system name</desc>\n      </prompt>\n    </field>\n    <field> \n      <name>description</name> \n      <help lang="en_US">@System_creation_description@</help>\n      <descriptions> \n        <desc>Description</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>false</required>\n      <prompt>\n        <desc>Enter the system description</desc>\n      </prompt>\n    </field>\n    <field> \n      <name>tempIpAddress</name> \n      <help lang="en_US">@System_creation_ip@</help>\n      <descriptions> \n        <desc>Network Address</desc> \n      </descriptions> \n      <prompt>\n        <desc>Enter the system network address</desc>\n      </prompt>\n      <type>str</type> \n      <default></default> \n      <required>true</required>\n    </field>\n    <field>\n      <name>requiredNetwork</name>\n      <help lang="en_US">@System_creation_required_net@</help>\n      <required>false</required>\n      <multiple>True</multiple>\n      <descriptions>\n        <desc>Manage Via this Address Only</desc>\n      </descriptions>\n      <enumeratedType>\n        <describedValue>\n          <descriptions>\n            <desc></desc>\n          </descriptions>\n          <key>true</key>\n        </describedValue>\n      </enumeratedType>\n      <default>false</default>\n    </field>\n  </dataFields> \n</descriptor>
2	infrastructure-management-node	rPath Update Service (Infrastructure)	2011-10-05 13:38:31.716827-04	t	<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> \n  <metadata>\n  </metadata> \n  <dataFields>\n    <field> \n      <name>name</name> \n      <help lang="en_US">@Management_node_creation_name@</help>\n      <descriptions> \n        <desc>System Name</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>true</required>\n      <prompt>\n        <desc>Enter the system name</desc>\n      </prompt>\n    </field>\n    <field> \n      <name>description</name> \n      <help lang="en_US">@Management_node_creation_description@</help>\n      <descriptions> \n        <desc>Description</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>false</required>\n      <prompt>\n        <desc>Enter the system description</desc>\n      </prompt>\n    </field>\n    <field> \n      <name>tempIpAddress</name> \n      <help lang="en_US">@Management_node_creation_ip@</help>\n      <descriptions> \n        <desc>Network Address</desc> \n      </descriptions> \n      <prompt>\n        <desc>Enter the system network address</desc>\n      </prompt>\n      <type>str</type> \n      <default></default> \n      <required>true</required>\n    </field>\n    <field> \n      <name>zoneName</name> \n      <help lang="en_US">@Management_node_zone_creation_name@</help>\n      <descriptions> \n        <desc>Zone Name</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>true</required>\n      <prompt>\n        <desc>Enter the name of the zone</desc>\n      </prompt>\n    </field>\n    <field> \n      <name>zoneDescription</name> \n      <help lang="en_US">@Management_node_zone_creation_description@</help>\n      <descriptions> \n        <desc>Zone Description</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>false</required>\n      <prompt>\n        <desc>Enter a description of the zone</desc>\n      </prompt>\n    </field>\n  </dataFields> \n</descriptor>
3	infrastructure-windows-build-node	rPath Windows Build Service (Infrastructure)	2011-10-05 13:38:31.717954-04	t	<descriptor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.rpath.com/permanent/descriptor-1.0.xsd" xsi:schemaLocation="http://www.rpath.com/permanent/descriptor-1.0.xsd descriptor-1.0.xsd"> \n  <metadata>\n  </metadata> \n  <dataFields>\n    <field> \n      <name>name</name> \n      <help lang="en_US">@Windows_build_node_creation_name@</help>\n      <descriptions> \n        <desc>System Name</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>true</required>\n      <prompt>\n        <desc>Enter the system name.</desc>\n      </prompt>\n    </field>\n    <field> \n      <name>description</name> \n      <help lang="en_US">@Windows_build_node_creation_description@</help>\n      <descriptions> \n        <desc>Description</desc> \n      </descriptions> \n      <type>str</type> \n      <default></default>\n      <required>false</required>\n      <prompt>\n        <desc>Enter the system description</desc>\n      </prompt>\n    </field>\n    <field> \n      <name>tempIpAddress</name> \n      <help lang="en_US">@Windows_build_node_creation_ip@</help>\n      <descriptions> \n        <desc>Network Address</desc> \n      </descriptions> \n      <prompt>\n        <desc>Enter the system network address</desc>\n      </prompt>\n      <type>str</type> \n      <default></default> \n      <required>true</required>\n    </field>\n  </dataFields> \n</descriptor>
\.


--
-- Data for Name: inventory_trove; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_trove (trove_id, name, version_id, flavor, is_top_level, last_available_update_refresh, out_of_date) FROM stdin;
\.


--
-- Data for Name: inventory_trove_available_updates; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_trove_available_updates (id, trove_id, version_id) FROM stdin;
\.


--
-- Data for Name: inventory_version; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_version (version_id, "full", label, revision, ordering, flavor) FROM stdin;
\.


--
-- Data for Name: inventory_zone; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_zone (zone_id, name, description, created_date) FROM stdin;
1	Local rBuilder	Local rBuilder management zone	2011-10-05 13:38:31.749712-04
\.


--
-- Data for Name: inventory_zone_management_node; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY inventory_zone_management_node (system_ptr_id, local, zone_id, node_jid) FROM stdin;
\.


--
-- Data for Name: job_history; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY job_history (job_history_id, job_id, "timestamp", content) FROM stdin;
\.


--
-- Data for Name: job_results; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY job_results (job_result_id, job_id, data) FROM stdin;
\.


--
-- Data for Name: job_states; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY job_states (job_state_id, name) FROM stdin;
1	Queued
2	Running
3	Completed
4	Failed
\.


--
-- Data for Name: job_system; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY job_system (job_id, system_id) FROM stdin;
\.


--
-- Data for Name: job_target; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY job_target (job_id, targetid) FROM stdin;
\.


--
-- Data for Name: job_types; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY job_types (job_type_id, name, description) FROM stdin;
1	instance-launch	Instance Launch
2	platform-load	Platform Load
3	software-version-refresh	Software Version Refresh
4	instance-update	Update Instance
\.


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY jobs (job_id, job_type_id, job_state_id, job_uuid, created_by, created, modified, expiration, ttl, pid, message, error_response, rest_uri, rest_method_id, rest_args) FROM stdin;
\.


--
-- Data for Name: labels; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY labels (labelid, projectid, label, url, authtype, username, password, entitlement) FROM stdin;
\.


--
-- Data for Name: latestcommit; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY latestcommit (projectid, committime) FROM stdin;
\.


--
-- Data for Name: membershiprequests; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY membershiprequests (projectid, userid, comments) FROM stdin;
\.


--
-- Data for Name: newscache; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY newscache (itemid, title, pubdate, content, link, category) FROM stdin;
\.


--
-- Data for Name: newscacheinfo; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY newscacheinfo (age, feedlink) FROM stdin;
\.


--
-- Data for Name: outboundmirrors; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY outboundmirrors (outboundmirrorid, sourceprojectid, targetlabels, alllabels, recurse, matchstrings, mirrororder, fullsync, usereleases) FROM stdin;
\.


--
-- Data for Name: outboundmirrorsupdateservices; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY outboundmirrorsupdateservices (outboundmirrorid, updateserviceid) FROM stdin;
\.


--
-- Data for Name: packageindex; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY packageindex (pkgid, projectid, name, version, servername, branchname, issource) FROM stdin;
\.


--
-- Data for Name: packageindexmark; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY packageindexmark (mark) FROM stdin;
0
\.


--
-- Data for Name: pki_certificates; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY pki_certificates (fingerprint, purpose, is_ca, x509_pem, pkey_pem, issuer_fingerprint, ca_serial_index, time_issued, time_expired) FROM stdin;
\.


--
-- Data for Name: platforms; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY platforms (platformid, label, mode, enabled, projectid, platformname, configurable, abstract, isfromdisk, time_refreshed) FROM stdin;
\.


--
-- Data for Name: platformscontentsourcetypes; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY platformscontentsourcetypes (platformid, contentsourcetype) FROM stdin;
\.


--
-- Data for Name: platformsourcedata; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY platformsourcedata (platformsourceid, name, value, datatype) FROM stdin;
\.


--
-- Data for Name: platformsources; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY platformsources (platformsourceid, name, shortname, defaultsource, contentsourcetype, orderindex) FROM stdin;
\.


--
-- Data for Name: platformsplatformsources; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY platformsplatformsources (platformid, platformsourceid) FROM stdin;
\.


--
-- Data for Name: popularprojects; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY popularprojects (projectid, rank) FROM stdin;
\.


--
-- Data for Name: productversions; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY productversions (productversionid, projectid, namespace, name, description, timecreated) FROM stdin;
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY projects (projectid, creatorid, name, hostname, shortname, domainname, fqdn, namespace, projecturl, description, disabled, hidden, external, isappliance, timecreated, timemodified, commitemail, prodtype, version, backupexternal, database) FROM stdin;
\.


--
-- Data for Name: projectusers; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY projectusers (projectid, userid, level) FROM stdin;
\.


--
-- Data for Name: publishedreleases; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY publishedreleases (pubreleaseid, projectid, name, version, description, timecreated, createdby, timeupdated, updatedby, timepublished, publishedby, shouldmirror, timemirrored) FROM stdin;
\.


--
-- Data for Name: querysets_filterentry; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY querysets_filterentry (filter_entry_id, field, operator, value) FROM stdin;
1	current_state.name	EQUAL	responsive
2	current_state.name	IN	(unmanaged,unmanaged-credentials,registered,non-responsive-unknown,non-responsive-net,non-responsive-host,non-responsive-shutdown,non-responsive-suspended,non-responsive-credentials)
3	target	IS_NULL	True
\.


--
-- Data for Name: querysets_inclusionmethod; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY querysets_inclusionmethod (inclusion_method_id, name) FROM stdin;
1	chosen
2	filtered
\.


--
-- Data for Name: querysets_queryset; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY querysets_queryset (query_set_id, name, description, created_date, modified_date, resource_type, can_modify) FROM stdin;
1	All Systems	All Systems	2011-10-05 13:38:31.895832-04	2011-10-05 13:38:31.895869-04	system	f
2	Active Systems	Active Systems	2011-10-05 13:38:31.89589-04	2011-10-05 13:38:31.895903-04	system	f
3	Inactive Systems	Inactive Systems	2011-10-05 13:38:31.895918-04	2011-10-05 13:38:31.895931-04	system	f
4	Physical Systems	Physical Systems	2011-10-05 13:38:31.895946-04	2011-10-05 13:38:31.895959-04	system	f
\.


--
-- Data for Name: querysets_queryset_children; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY querysets_queryset_children (id, from_queryset_id, to_queryset_id) FROM stdin;
1	1	2
2	1	3
\.


--
-- Data for Name: querysets_queryset_filter_entries; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY querysets_queryset_filter_entries (id, queryset_id, filterentry_id) FROM stdin;
1	2	1
2	3	2
3	4	3
\.


--
-- Data for Name: querysets_querytag; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY querysets_querytag (query_tag_id, query_set_id, name) FROM stdin;
1	1	query-tag-All_Systems-1
2	2	query-tag-Active_Systems-2
3	3	query-tag-Inactive_Systems-3
4	4	query-tag-Physical_Systems-4
\.


--
-- Data for Name: querysets_systemtag; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY querysets_systemtag (system_tag_id, system_id, query_tag_id, inclusion_method_id) FROM stdin;
\.


--
-- Data for Name: repnamemap; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY repnamemap (fromname, toname) FROM stdin;
\.


--
-- Data for Name: repositorylogstatus; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY repositorylogstatus (logname, inode, logoffset) FROM stdin;
\.


--
-- Data for Name: rest_methods; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY rest_methods (rest_method_id, name) FROM stdin;
1	POST
2	PUT
3	DELETE
\.


--
-- Data for Name: sessions; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY sessions (sessidx, sid, data) FROM stdin;
\.


--
-- Data for Name: systemupdate; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY systemupdate (systemupdateid, servername, repositoryname, updatetime, updateuser) FROM stdin;
\.


--
-- Data for Name: targetcredentials; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY targetcredentials (targetcredentialsid, credentials) FROM stdin;
\.


--
-- Data for Name: targetdata; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY targetdata (targetid, name, value) FROM stdin;
\.


--
-- Data for Name: targetimagesdeployed; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY targetimagesdeployed (id, targetid, fileid, targetimageid) FROM stdin;
\.


--
-- Data for Name: targets; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY targets (targetid, targettype, targetname) FROM stdin;
\.


--
-- Data for Name: targetusercredentials; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY targetusercredentials (id, targetid, userid, targetcredentialsid) FROM stdin;
\.


--
-- Data for Name: topprojects; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY topprojects (projectid, rank) FROM stdin;
\.


--
-- Data for Name: updateservices; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY updateservices (updateserviceid, hostname, description, mirroruser, mirrorpassword) FROM stdin;
\.


--
-- Data for Name: urldownloads; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY urldownloads (urlid, timedownloaded, ip) FROM stdin;
\.


--
-- Data for Name: useit; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY useit (itemid, name, link) FROM stdin;
\.


--
-- Data for Name: userdata; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY userdata (userid, name, value, datatype) FROM stdin;
\.


--
-- Data for Name: usergroupmembers; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY usergroupmembers (usergroupid, userid) FROM stdin;
\.


--
-- Data for Name: usergroups; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY usergroups (usergroupid, usergroup) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: conary
--

COPY users (userid, username, fullname, salt, passwd, email, displayemail, timecreated, timeaccessed, active, blurb) FROM stdin;
\.


--
-- Name: appliancespotlight_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY appliancespotlight
    ADD CONSTRAINT appliancespotlight_pkey PRIMARY KEY (itemid);


--
-- Name: builddata_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY builddata
    ADD CONSTRAINT builddata_pkey PRIMARY KEY (buildid, name);


--
-- Name: buildfiles_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY buildfiles
    ADD CONSTRAINT buildfiles_pkey PRIMARY KEY (fileid);


--
-- Name: buildfilesurlsmap_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY buildfilesurlsmap
    ADD CONSTRAINT buildfilesurlsmap_pkey PRIMARY KEY (fileid, urlid);


--
-- Name: builds_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_pkey PRIMARY KEY (buildid);


--
-- Name: changelog_change_log_entry_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY changelog_change_log_entry
    ADD CONSTRAINT changelog_change_log_entry_pkey PRIMARY KEY (change_log_entry_id);


--
-- Name: changelog_change_log_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY changelog_change_log
    ADD CONSTRAINT changelog_change_log_pkey PRIMARY KEY (change_log_id);


--
-- Name: ci_rhn_channels_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_rhn_channels
    ADD CONSTRAINT ci_rhn_channels_pkey PRIMARY KEY (channel_id);


--
-- Name: ci_rhn_errata_nevra_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_rhn_errata_nevra_channel
    ADD CONSTRAINT ci_rhn_errata_nevra_channel_pkey PRIMARY KEY (errata_id, nevra_id, channel_id);


--
-- Name: ci_rhn_errata_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_rhn_errata
    ADD CONSTRAINT ci_rhn_errata_pkey PRIMARY KEY (errata_id);


--
-- Name: ci_rhn_nevra_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_rhn_nevra
    ADD CONSTRAINT ci_rhn_nevra_pkey PRIMARY KEY (nevra_id);


--
-- Name: ci_rhn_package_failed_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_rhn_package_failed
    ADD CONSTRAINT ci_rhn_package_failed_pkey PRIMARY KEY (package_failed_id);


--
-- Name: ci_rhn_packages_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_rhn_packages
    ADD CONSTRAINT ci_rhn_packages_pkey PRIMARY KEY (package_id);


--
-- Name: ci_yum_packages_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_yum_packages
    ADD CONSTRAINT ci_yum_packages_pkey PRIMARY KEY (package_id);


--
-- Name: ci_yum_repositories_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_yum_repositories
    ADD CONSTRAINT ci_yum_repositories_pkey PRIMARY KEY (yum_repository_id);


--
-- Name: ci_yum_repository_package_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY ci_yum_repository_package
    ADD CONSTRAINT ci_yum_repository_package_pkey PRIMARY KEY (yum_repository_id, package_id);


--
-- Name: django_redirect_old_path_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY django_redirect
    ADD CONSTRAINT django_redirect_old_path_key UNIQUE (old_path);


--
-- Name: django_redirect_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY django_redirect
    ADD CONSTRAINT django_redirect_pkey PRIMARY KEY (id);


--
-- Name: django_site_domain_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY django_site
    ADD CONSTRAINT django_site_domain_key UNIQUE (domain);


--
-- Name: django_site_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY django_site
    ADD CONSTRAINT django_site_name_key UNIQUE (name);


--
-- Name: django_site_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY django_site
    ADD CONSTRAINT django_site_pkey PRIMARY KEY (id);


--
-- Name: filesurls_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY filesurls
    ADD CONSTRAINT filesurls_pkey PRIMARY KEY (urlid);


--
-- Name: frontpageselections_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY frontpageselections
    ADD CONSTRAINT frontpageselections_pkey PRIMARY KEY (itemid);


--
-- Name: inboundmirrors_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inboundmirrors
    ADD CONSTRAINT inboundmirrors_pkey PRIMARY KEY (inboundmirrorid);


--
-- Name: inventory_event_type_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_event_type
    ADD CONSTRAINT inventory_event_type_name_key UNIQUE (name);


--
-- Name: inventory_event_type_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_event_type
    ADD CONSTRAINT inventory_event_type_pkey PRIMARY KEY (event_type_id);


--
-- Name: inventory_job_job_uuid_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_job
    ADD CONSTRAINT inventory_job_job_uuid_key UNIQUE (job_uuid);


--
-- Name: inventory_job_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_job
    ADD CONSTRAINT inventory_job_pkey PRIMARY KEY (job_id);


--
-- Name: inventory_job_state_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_job_state
    ADD CONSTRAINT inventory_job_state_name_key UNIQUE (name);


--
-- Name: inventory_job_state_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_job_state
    ADD CONSTRAINT inventory_job_state_pkey PRIMARY KEY (job_state_id);


--
-- Name: inventory_management_interface_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_management_interface
    ADD CONSTRAINT inventory_management_interface_name_key UNIQUE (name);


--
-- Name: inventory_management_interface_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_management_interface
    ADD CONSTRAINT inventory_management_interface_pkey PRIMARY KEY (management_interface_id);


--
-- Name: inventory_stage_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_stage
    ADD CONSTRAINT inventory_stage_pkey PRIMARY KEY (stage_id);


--
-- Name: inventory_system_event_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_event
    ADD CONSTRAINT inventory_system_event_pkey PRIMARY KEY (system_event_id);


--
-- Name: inventory_system_installed_software_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_installed_software
    ADD CONSTRAINT inventory_system_installed_software_pkey PRIMARY KEY (id);


--
-- Name: inventory_system_installed_software_system_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_installed_software
    ADD CONSTRAINT inventory_system_installed_software_system_id_key UNIQUE (system_id, trove_id);


--
-- Name: inventory_system_job_event_uuid_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_job
    ADD CONSTRAINT inventory_system_job_event_uuid_key UNIQUE (event_uuid);


--
-- Name: inventory_system_job_job_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_job
    ADD CONSTRAINT inventory_system_job_job_id_key UNIQUE (job_id);


--
-- Name: inventory_system_job_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_job
    ADD CONSTRAINT inventory_system_job_pkey PRIMARY KEY (system_job_id);


--
-- Name: inventory_system_log_entry_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_log_entry
    ADD CONSTRAINT inventory_system_log_entry_pkey PRIMARY KEY (system_log_entry_id);


--
-- Name: inventory_system_log_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_log
    ADD CONSTRAINT inventory_system_log_pkey PRIMARY KEY (system_log_id);


--
-- Name: inventory_system_network_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_network
    ADD CONSTRAINT inventory_system_network_pkey PRIMARY KEY (network_id);


--
-- Name: inventory_system_network_system_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_network
    ADD CONSTRAINT inventory_system_network_system_id_key UNIQUE (system_id, ip_address);


--
-- Name: inventory_system_network_system_id_key1; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_network
    ADD CONSTRAINT inventory_system_network_system_id_key1 UNIQUE (system_id, ipv6_address);


--
-- Name: inventory_system_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_pkey PRIMARY KEY (system_id);


--
-- Name: inventory_system_state_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_state
    ADD CONSTRAINT inventory_system_state_name_key UNIQUE (name);


--
-- Name: inventory_system_state_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_state
    ADD CONSTRAINT inventory_system_state_pkey PRIMARY KEY (system_state_id);


--
-- Name: inventory_system_target_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_target_credentials
    ADD CONSTRAINT inventory_system_target_credentials_pkey PRIMARY KEY (id);


--
-- Name: inventory_system_target_credentials_system_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_target_credentials
    ADD CONSTRAINT inventory_system_target_credentials_system_id_key UNIQUE (system_id, credentials_id);


--
-- Name: inventory_system_type_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_type
    ADD CONSTRAINT inventory_system_type_name_key UNIQUE (name);


--
-- Name: inventory_system_type_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_system_type
    ADD CONSTRAINT inventory_system_type_pkey PRIMARY KEY (system_type_id);


--
-- Name: inventory_trove_available_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_trove_available_updates
    ADD CONSTRAINT inventory_trove_available_updates_pkey PRIMARY KEY (id);


--
-- Name: inventory_trove_available_updates_trove_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_trove_available_updates
    ADD CONSTRAINT inventory_trove_available_updates_trove_id_key UNIQUE (trove_id, version_id);


--
-- Name: inventory_trove_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_trove
    ADD CONSTRAINT inventory_trove_name_key UNIQUE (name, version_id, flavor);


--
-- Name: inventory_trove_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_trove
    ADD CONSTRAINT inventory_trove_pkey PRIMARY KEY (trove_id);


--
-- Name: inventory_version_full_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_version
    ADD CONSTRAINT inventory_version_full_key UNIQUE ("full", ordering, flavor);


--
-- Name: inventory_version_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_version
    ADD CONSTRAINT inventory_version_pkey PRIMARY KEY (version_id);


--
-- Name: inventory_zone_management_node_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_zone_management_node
    ADD CONSTRAINT inventory_zone_management_node_pkey PRIMARY KEY (system_ptr_id);


--
-- Name: inventory_zone_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_zone
    ADD CONSTRAINT inventory_zone_name_key UNIQUE (name);


--
-- Name: inventory_zone_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY inventory_zone
    ADD CONSTRAINT inventory_zone_pkey PRIMARY KEY (zone_id);


--
-- Name: job_history_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY job_history
    ADD CONSTRAINT job_history_pkey PRIMARY KEY (job_history_id);


--
-- Name: job_results_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY job_results
    ADD CONSTRAINT job_results_pkey PRIMARY KEY (job_result_id);


--
-- Name: job_states_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY job_states
    ADD CONSTRAINT job_states_name_key UNIQUE (name);


--
-- Name: job_states_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY job_states
    ADD CONSTRAINT job_states_pkey PRIMARY KEY (job_state_id);


--
-- Name: job_types_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY job_types
    ADD CONSTRAINT job_types_name_key UNIQUE (name);


--
-- Name: job_types_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY job_types
    ADD CONSTRAINT job_types_pkey PRIMARY KEY (job_type_id);


--
-- Name: jobs_job_uuid_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_job_uuid_key UNIQUE (job_uuid);


--
-- Name: jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (job_id);


--
-- Name: labels_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY labels
    ADD CONSTRAINT labels_pkey PRIMARY KEY (labelid);


--
-- Name: membershiprequests_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY membershiprequests
    ADD CONSTRAINT membershiprequests_pkey PRIMARY KEY (projectid, userid);


--
-- Name: newscache_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY newscache
    ADD CONSTRAINT newscache_pkey PRIMARY KEY (itemid);


--
-- Name: outboundmirrors_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY outboundmirrors
    ADD CONSTRAINT outboundmirrors_pkey PRIMARY KEY (outboundmirrorid);


--
-- Name: outboundmirrorsupdateservices_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY outboundmirrorsupdateservices
    ADD CONSTRAINT outboundmirrorsupdateservices_pkey PRIMARY KEY (outboundmirrorid, updateserviceid);


--
-- Name: packageindex_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY packageindex
    ADD CONSTRAINT packageindex_pkey PRIMARY KEY (pkgid);


--
-- Name: pki_certificates_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY pki_certificates
    ADD CONSTRAINT pki_certificates_pkey PRIMARY KEY (fingerprint);


--
-- Name: platforms_label_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY platforms
    ADD CONSTRAINT platforms_label_key UNIQUE (label);


--
-- Name: platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY platforms
    ADD CONSTRAINT platforms_pkey PRIMARY KEY (platformid);


--
-- Name: platformsourcedata_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY platformsourcedata
    ADD CONSTRAINT platformsourcedata_pkey PRIMARY KEY (platformsourceid, name);


--
-- Name: platformsources_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY platformsources
    ADD CONSTRAINT platformsources_pkey PRIMARY KEY (platformsourceid);


--
-- Name: platformsources_shortname_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY platformsources
    ADD CONSTRAINT platformsources_shortname_key UNIQUE (shortname);


--
-- Name: productversions_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY productversions
    ADD CONSTRAINT productversions_pkey PRIMARY KEY (productversionid);


--
-- Name: projects_hostname_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_hostname_key UNIQUE (hostname);


--
-- Name: projects_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (projectid);


--
-- Name: projects_shortname_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_shortname_key UNIQUE (shortname);


--
-- Name: projectusers_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY projectusers
    ADD CONSTRAINT projectusers_pkey PRIMARY KEY (projectid, userid);


--
-- Name: publishedreleases_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY publishedreleases
    ADD CONSTRAINT publishedreleases_pkey PRIMARY KEY (pubreleaseid);


--
-- Name: querysets_filterentry_field_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_filterentry
    ADD CONSTRAINT querysets_filterentry_field_key UNIQUE (field, operator, value);


--
-- Name: querysets_filterentry_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_filterentry
    ADD CONSTRAINT querysets_filterentry_pkey PRIMARY KEY (filter_entry_id);


--
-- Name: querysets_inclusionmethod_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_inclusionmethod
    ADD CONSTRAINT querysets_inclusionmethod_name_key UNIQUE (name);


--
-- Name: querysets_inclusionmethod_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_inclusionmethod
    ADD CONSTRAINT querysets_inclusionmethod_pkey PRIMARY KEY (inclusion_method_id);


--
-- Name: querysets_queryset_children_from_queryset_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_queryset_children
    ADD CONSTRAINT querysets_queryset_children_from_queryset_id_key UNIQUE (from_queryset_id, to_queryset_id);


--
-- Name: querysets_queryset_children_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_queryset_children
    ADD CONSTRAINT querysets_queryset_children_pkey PRIMARY KEY (id);


--
-- Name: querysets_queryset_filter_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_queryset_filter_entries
    ADD CONSTRAINT querysets_queryset_filter_entries_pkey PRIMARY KEY (id);


--
-- Name: querysets_queryset_filter_entries_queryset_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_queryset_filter_entries
    ADD CONSTRAINT querysets_queryset_filter_entries_queryset_id_key UNIQUE (queryset_id, filterentry_id);


--
-- Name: querysets_queryset_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_queryset
    ADD CONSTRAINT querysets_queryset_name_key UNIQUE (name);


--
-- Name: querysets_queryset_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_queryset
    ADD CONSTRAINT querysets_queryset_pkey PRIMARY KEY (query_set_id);


--
-- Name: querysets_querytag_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_querytag
    ADD CONSTRAINT querysets_querytag_name_key UNIQUE (name);


--
-- Name: querysets_querytag_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_querytag
    ADD CONSTRAINT querysets_querytag_pkey PRIMARY KEY (query_tag_id);


--
-- Name: querysets_querytag_query_set_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_querytag
    ADD CONSTRAINT querysets_querytag_query_set_id_key UNIQUE (query_set_id);


--
-- Name: querysets_systemtag_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_systemtag
    ADD CONSTRAINT querysets_systemtag_pkey PRIMARY KEY (system_tag_id);


--
-- Name: querysets_systemtag_system_id_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY querysets_systemtag
    ADD CONSTRAINT querysets_systemtag_system_id_key UNIQUE (system_id, query_tag_id, inclusion_method_id);


--
-- Name: repnamemap_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY repnamemap
    ADD CONSTRAINT repnamemap_pkey PRIMARY KEY (fromname, toname);


--
-- Name: repositorylogstatus_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY repositorylogstatus
    ADD CONSTRAINT repositorylogstatus_pkey PRIMARY KEY (logname);


--
-- Name: rest_methods_name_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY rest_methods
    ADD CONSTRAINT rest_methods_name_key UNIQUE (name);


--
-- Name: rest_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY rest_methods
    ADD CONSTRAINT rest_methods_pkey PRIMARY KEY (rest_method_id);


--
-- Name: sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (sessidx);


--
-- Name: sessions_sid_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY sessions
    ADD CONSTRAINT sessions_sid_key UNIQUE (sid);


--
-- Name: systemupdate_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY systemupdate
    ADD CONSTRAINT systemupdate_pkey PRIMARY KEY (systemupdateid);


--
-- Name: targetcredentials_credentials_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY targetcredentials
    ADD CONSTRAINT targetcredentials_credentials_key UNIQUE (credentials);


--
-- Name: targetcredentials_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY targetcredentials
    ADD CONSTRAINT targetcredentials_pkey PRIMARY KEY (targetcredentialsid);


--
-- Name: targetdata_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY targetdata
    ADD CONSTRAINT targetdata_pkey PRIMARY KEY (targetid, name);


--
-- Name: targetimagesdeployed_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY targetimagesdeployed
    ADD CONSTRAINT targetimagesdeployed_pkey PRIMARY KEY (id);


--
-- Name: targets_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY targets
    ADD CONSTRAINT targets_pkey PRIMARY KEY (targetid);


--
-- Name: targetusercredentials_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY targetusercredentials
    ADD CONSTRAINT targetusercredentials_pkey PRIMARY KEY (id);


--
-- Name: targetusercredentials_targetid_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY targetusercredentials
    ADD CONSTRAINT targetusercredentials_targetid_key UNIQUE (targetid, userid);


--
-- Name: updateservices_hostname_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY updateservices
    ADD CONSTRAINT updateservices_hostname_key UNIQUE (hostname);


--
-- Name: updateservices_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY updateservices
    ADD CONSTRAINT updateservices_pkey PRIMARY KEY (updateserviceid);


--
-- Name: useit_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY useit
    ADD CONSTRAINT useit_pkey PRIMARY KEY (itemid);


--
-- Name: userdata_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY userdata
    ADD CONSTRAINT userdata_pkey PRIMARY KEY (userid, name);


--
-- Name: usergroupmembers_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY usergroupmembers
    ADD CONSTRAINT usergroupmembers_pkey PRIMARY KEY (usergroupid, userid);


--
-- Name: usergroups_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY usergroups
    ADD CONSTRAINT usergroups_pkey PRIMARY KEY (usergroupid);


--
-- Name: usergroups_usergroup_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY usergroups
    ADD CONSTRAINT usergroups_usergroup_key UNIQUE (usergroup);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (userid);


--
-- Name: users_username_key; Type: CONSTRAINT; Schema: public; Owner: conary; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: buildprojectididx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX buildprojectididx ON builds USING btree (projectid);


--
-- Name: buildpubreleaseididx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX buildpubreleaseididx ON builds USING btree (pubreleaseid);


--
-- Name: ci_rhn_channel_package_cid_pid_idx_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX ci_rhn_channel_package_cid_pid_idx_uq ON ci_rhn_channel_package USING btree (channel_id, package_id);


--
-- Name: ci_rhn_channel_package_pid_cid_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX ci_rhn_channel_package_pid_cid_idx ON ci_rhn_channel_package USING btree (package_id, channel_id);


--
-- Name: ci_rhn_channels_label_idx_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX ci_rhn_channels_label_idx_uq ON ci_rhn_channels USING btree (label);


--
-- Name: ci_rhn_errata_channel_cid_eid_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX ci_rhn_errata_channel_cid_eid_idx ON ci_rhn_errata_channel USING btree (channel_id, errata_id);


--
-- Name: ci_rhn_errata_channel_eid_cid_idx_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX ci_rhn_errata_channel_eid_cid_idx_uq ON ci_rhn_errata_channel USING btree (errata_id, channel_id);


--
-- Name: ci_rhn_nevra_n_e_v_r_a_idx_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX ci_rhn_nevra_n_e_v_r_a_idx_uq ON ci_rhn_nevra USING btree (name, epoch, version, release, arch);


--
-- Name: ci_rhn_packages_nevra_id_last_modified_idx_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX ci_rhn_packages_nevra_id_last_modified_idx_uq ON ci_rhn_packages USING btree (nevra_id, last_modified);


--
-- Name: ci_rhn_packages_nevra_id_sha1sum_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX ci_rhn_packages_nevra_id_sha1sum_idx ON ci_rhn_packages USING btree (nevra_id, sha1sum);


--
-- Name: ci_yum_packages_nevra_id_checksum_idx_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX ci_yum_packages_nevra_id_checksum_idx_uq ON ci_yum_packages USING btree (nevra_id, checksum, checksum_type);


--
-- Name: ci_yum_repositories_label_idx_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX ci_yum_repositories_label_idx_uq ON ci_yum_repositories USING btree (label);


--
-- Name: commitsprojectidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX commitsprojectidx ON commits USING btree (projectid);


--
-- Name: inboundmirrorsprojectididx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inboundmirrorsprojectididx ON inboundmirrors USING btree (targetprojectid);


--
-- Name: inventory_system_event_event_type_id; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_event_event_type_id ON inventory_system_event USING btree (event_type_id);


--
-- Name: inventory_system_event_priority; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_event_priority ON inventory_system_event USING btree (priority);


--
-- Name: inventory_system_event_system_id; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_event_system_id ON inventory_system_event USING btree (system_id);


--
-- Name: inventory_system_event_time_enabled; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_event_time_enabled ON inventory_system_event USING btree (time_enabled);


--
-- Name: inventory_system_log_system_id_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_log_system_id_idx ON inventory_system_log USING btree (system_id);


--
-- Name: inventory_system_network_dns_name_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_network_dns_name_idx ON inventory_system_network USING btree (dns_name);


--
-- Name: inventory_system_network_system_id_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_network_system_id_idx ON inventory_system_network USING btree (system_id);


--
-- Name: inventory_system_target_id_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX inventory_system_target_id_idx ON inventory_system USING btree (target_id);


--
-- Name: labelspackageidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX labelspackageidx ON labels USING btree (projectid);


--
-- Name: latestcommittimestamp; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX latestcommittimestamp ON latestcommit USING btree (projectid, committime);


--
-- Name: outboundmirrorsprojectididx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX outboundmirrorsprojectididx ON outboundmirrors USING btree (sourceprojectid);


--
-- Name: packageindex_project_name_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX packageindex_project_name_idx ON packageindex USING btree (projectid, name);


--
-- Name: packageindexnameidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX packageindexnameidx ON packageindex USING btree (name, version);


--
-- Name: packageindexprojectidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX packageindexprojectidx ON packageindex USING btree (projectid);


--
-- Name: packageindexserverbranchname; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX packageindexserverbranchname ON packageindex USING btree (servername, branchname);


--
-- Name: platformscontentsourcetypes_platformid_contentsourcetype_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX platformscontentsourcetypes_platformid_contentsourcetype_uq ON platformscontentsourcetypes USING btree (platformid, contentsourcetype);


--
-- Name: platformsources_platformsourceid_defaultsource_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX platformsources_platformsourceid_defaultsource_uq ON platformsources USING btree (platformsourceid, defaultsource);


--
-- Name: platformsources_platformsourceid_orderindex_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX platformsources_platformsourceid_orderindex_uq ON platformsources USING btree (platformsourceid, orderindex);


--
-- Name: productversions_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX productversions_uq ON productversions USING btree (projectid, namespace, name);


--
-- Name: projectsdisabledidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX projectsdisabledidx ON projects USING btree (disabled);


--
-- Name: projectshiddenidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX projectshiddenidx ON projects USING btree (hidden);


--
-- Name: projectshostnameidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX projectshostnameidx ON projects USING btree (hostname);


--
-- Name: projectsshortnameidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX projectsshortnameidx ON projects USING btree (shortname);


--
-- Name: projectusersprojectidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX projectusersprojectidx ON projectusers USING btree (projectid);


--
-- Name: projectusersuseridx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX projectusersuseridx ON projectusers USING btree (userid);


--
-- Name: pubreleasesprojectididx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX pubreleasesprojectididx ON publishedreleases USING btree (projectid);


--
-- Name: repnamemap_fromname_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX repnamemap_fromname_idx ON repnamemap USING btree (fromname);


--
-- Name: repnamemap_toname_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX repnamemap_toname_idx ON repnamemap USING btree (toname);


--
-- Name: systemupdate_repo_idx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX systemupdate_repo_idx ON systemupdate USING btree (repositoryname);


--
-- Name: targets_type_name_uq; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE UNIQUE INDEX targets_type_name_uq ON targets USING btree (targettype, targetname);


--
-- Name: userdataidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX userdataidx ON userdata USING btree (userid);


--
-- Name: usersactiveidx; Type: INDEX; Schema: public; Owner: conary; Tablespace: 
--

CREATE INDEX usersactiveidx ON users USING btree (username, active);


--
-- Name: builddata_buildid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY builddata
    ADD CONSTRAINT builddata_buildid_fkey FOREIGN KEY (buildid) REFERENCES builds(buildid) ON DELETE CASCADE;


--
-- Name: buildfiles_buildid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY buildfiles
    ADD CONSTRAINT buildfiles_buildid_fkey FOREIGN KEY (buildid) REFERENCES builds(buildid) ON DELETE CASCADE;


--
-- Name: buildfilesurlsmap_fileid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY buildfilesurlsmap
    ADD CONSTRAINT buildfilesurlsmap_fileid_fkey FOREIGN KEY (fileid) REFERENCES buildfiles(fileid) ON DELETE CASCADE;


--
-- Name: buildfilesurlsmap_urlid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY buildfilesurlsmap
    ADD CONSTRAINT buildfilesurlsmap_urlid_fkey FOREIGN KEY (urlid) REFERENCES filesurls(urlid) ON DELETE CASCADE;


--
-- Name: builds_createdby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_createdby_fkey FOREIGN KEY (createdby) REFERENCES users(userid) ON DELETE SET NULL;


--
-- Name: builds_productversionid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_productversionid_fkey FOREIGN KEY (productversionid) REFERENCES productversions(productversionid) ON DELETE SET NULL;


--
-- Name: builds_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: builds_pubreleaseid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_pubreleaseid_fkey FOREIGN KEY (pubreleaseid) REFERENCES publishedreleases(pubreleaseid) ON DELETE SET NULL;


--
-- Name: builds_updatedby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY builds
    ADD CONSTRAINT builds_updatedby_fkey FOREIGN KEY (updatedby) REFERENCES users(userid) ON DELETE SET NULL;


--
-- Name: changelog_change_log_entry_change_log_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY changelog_change_log_entry
    ADD CONSTRAINT changelog_change_log_entry_change_log_id_fkey FOREIGN KEY (change_log_id) REFERENCES changelog_change_log(change_log_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_channel_package_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_channel_package
    ADD CONSTRAINT ci_rhn_channel_package_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES ci_rhn_channels(channel_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_channel_package_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_channel_package
    ADD CONSTRAINT ci_rhn_channel_package_package_id_fkey FOREIGN KEY (package_id) REFERENCES ci_rhn_packages(package_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_errata_channel_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_errata_channel
    ADD CONSTRAINT ci_rhn_errata_channel_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES ci_rhn_channels(channel_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_errata_channel_errata_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_errata_channel
    ADD CONSTRAINT ci_rhn_errata_channel_errata_id_fkey FOREIGN KEY (errata_id) REFERENCES ci_rhn_errata(errata_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_errata_nevra_channel_channel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_errata_nevra_channel
    ADD CONSTRAINT ci_rhn_errata_nevra_channel_channel_id_fkey FOREIGN KEY (channel_id) REFERENCES ci_rhn_channels(channel_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_errata_nevra_channel_errata_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_errata_nevra_channel
    ADD CONSTRAINT ci_rhn_errata_nevra_channel_errata_id_fkey FOREIGN KEY (errata_id) REFERENCES ci_rhn_errata(errata_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_errata_nevra_channel_nevra_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_errata_nevra_channel
    ADD CONSTRAINT ci_rhn_errata_nevra_channel_nevra_id_fkey FOREIGN KEY (nevra_id) REFERENCES ci_rhn_nevra(nevra_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_package_failed_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_package_failed
    ADD CONSTRAINT ci_rhn_package_failed_package_id_fkey FOREIGN KEY (package_id) REFERENCES ci_rhn_packages(package_id) ON DELETE CASCADE;


--
-- Name: ci_rhn_packages_nevra_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_rhn_packages
    ADD CONSTRAINT ci_rhn_packages_nevra_id_fkey FOREIGN KEY (nevra_id) REFERENCES ci_rhn_nevra(nevra_id) ON DELETE CASCADE;


--
-- Name: ci_yum_packages_nevra_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_yum_packages
    ADD CONSTRAINT ci_yum_packages_nevra_id_fkey FOREIGN KEY (nevra_id) REFERENCES ci_rhn_nevra(nevra_id) ON DELETE CASCADE;


--
-- Name: ci_yum_repository_package_package_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_yum_repository_package
    ADD CONSTRAINT ci_yum_repository_package_package_id_fkey FOREIGN KEY (package_id) REFERENCES ci_yum_packages(package_id) ON DELETE CASCADE;


--
-- Name: ci_yum_repository_package_yum_repository_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY ci_yum_repository_package
    ADD CONSTRAINT ci_yum_repository_package_yum_repository_id_fkey FOREIGN KEY (yum_repository_id) REFERENCES ci_yum_repositories(yum_repository_id) ON DELETE CASCADE;


--
-- Name: commits_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY commits
    ADD CONSTRAINT commits_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: commits_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY commits
    ADD CONSTRAINT commits_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE SET NULL;


--
-- Name: communityids_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY communityids
    ADD CONSTRAINT communityids_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: confirmations_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY confirmations
    ADD CONSTRAINT confirmations_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: django_redirect_site_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY django_redirect
    ADD CONSTRAINT django_redirect_site_id_fkey FOREIGN KEY (site_id) REFERENCES django_site(id);


--
-- Name: inboundmirrors_targetprojectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inboundmirrors
    ADD CONSTRAINT inboundmirrors_targetprojectid_fkey FOREIGN KEY (targetprojectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: inventory_job_event_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_job
    ADD CONSTRAINT inventory_job_event_type_id_fkey FOREIGN KEY (event_type_id) REFERENCES inventory_event_type(event_type_id);


--
-- Name: inventory_job_job_state_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_job
    ADD CONSTRAINT inventory_job_job_state_id_fkey FOREIGN KEY (job_state_id) REFERENCES inventory_job_state(job_state_id);


--
-- Name: inventory_stage_major_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_stage
    ADD CONSTRAINT inventory_stage_major_version_id_fkey FOREIGN KEY (major_version_id) REFERENCES productversions(productversionid) ON DELETE SET NULL;


--
-- Name: inventory_system_appliance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_appliance_id_fkey FOREIGN KEY (appliance_id) REFERENCES projects(projectid);


--
-- Name: inventory_system_current_state_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_current_state_id_fkey FOREIGN KEY (current_state_id) REFERENCES inventory_system_state(system_state_id);


--
-- Name: inventory_system_event_event_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_event
    ADD CONSTRAINT inventory_system_event_event_type_id_fkey FOREIGN KEY (event_type_id) REFERENCES inventory_event_type(event_type_id);


--
-- Name: inventory_system_event_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_event
    ADD CONSTRAINT inventory_system_event_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: inventory_system_installed_software_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_installed_software
    ADD CONSTRAINT inventory_system_installed_software_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: inventory_system_installed_software_trove_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_installed_software
    ADD CONSTRAINT inventory_system_installed_software_trove_id_fkey FOREIGN KEY (trove_id) REFERENCES inventory_trove(trove_id);


--
-- Name: inventory_system_job_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_job
    ADD CONSTRAINT inventory_system_job_job_id_fkey FOREIGN KEY (job_id) REFERENCES inventory_job(job_id) ON DELETE CASCADE;


--
-- Name: inventory_system_job_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_job
    ADD CONSTRAINT inventory_system_job_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: inventory_system_launching_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_launching_user_id_fkey FOREIGN KEY (launching_user_id) REFERENCES users(userid);


--
-- Name: inventory_system_log_entry_system_log_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_log_entry
    ADD CONSTRAINT inventory_system_log_entry_system_log_id_fkey FOREIGN KEY (system_log_id) REFERENCES inventory_system_log(system_log_id) ON DELETE CASCADE;


--
-- Name: inventory_system_log_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_log
    ADD CONSTRAINT inventory_system_log_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: inventory_system_major_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_major_version_id_fkey FOREIGN KEY (major_version_id) REFERENCES productversions(productversionid);


--
-- Name: inventory_system_management_interface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_management_interface_id_fkey FOREIGN KEY (management_interface_id) REFERENCES inventory_management_interface(management_interface_id);


--
-- Name: inventory_system_managing_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_managing_zone_id_fkey FOREIGN KEY (managing_zone_id) REFERENCES inventory_zone(zone_id);


--
-- Name: inventory_system_network_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_network
    ADD CONSTRAINT inventory_system_network_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: inventory_system_stage_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_stage_id_fkey FOREIGN KEY (stage_id) REFERENCES inventory_stage(stage_id);


--
-- Name: inventory_system_system_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_system_type_id_fkey FOREIGN KEY (system_type_id) REFERENCES inventory_system_type(system_type_id);


--
-- Name: inventory_system_target_credentials_credentials_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_target_credentials
    ADD CONSTRAINT inventory_system_target_credentials_credentials_id_fkey FOREIGN KEY (credentials_id) REFERENCES targetcredentials(targetcredentialsid) ON DELETE CASCADE;


--
-- Name: inventory_system_target_credentials_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system_target_credentials
    ADD CONSTRAINT inventory_system_target_credentials_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: inventory_system_target_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_system
    ADD CONSTRAINT inventory_system_target_id_fkey FOREIGN KEY (target_id) REFERENCES targets(targetid) ON DELETE SET NULL;


--
-- Name: inventory_trove_available_updates_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_trove_available_updates
    ADD CONSTRAINT inventory_trove_available_updates_version_id_fkey FOREIGN KEY (version_id) REFERENCES inventory_version(version_id) ON DELETE CASCADE;


--
-- Name: inventory_trove_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_trove
    ADD CONSTRAINT inventory_trove_version_id_fkey FOREIGN KEY (version_id) REFERENCES inventory_version(version_id) ON DELETE CASCADE;


--
-- Name: inventory_zone_management_node_system_ptr_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_zone_management_node
    ADD CONSTRAINT inventory_zone_management_node_system_ptr_id_fkey FOREIGN KEY (system_ptr_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: inventory_zone_management_node_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY inventory_zone_management_node
    ADD CONSTRAINT inventory_zone_management_node_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES inventory_zone(zone_id);


--
-- Name: job_history_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY job_history
    ADD CONSTRAINT job_history_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;


--
-- Name: job_results_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY job_results
    ADD CONSTRAINT job_results_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;


--
-- Name: job_system_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY job_system
    ADD CONSTRAINT job_system_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;


--
-- Name: job_system_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY job_system
    ADD CONSTRAINT job_system_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: job_target_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY job_target
    ADD CONSTRAINT job_target_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;


--
-- Name: job_target_targetid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY job_target
    ADD CONSTRAINT job_target_targetid_fkey FOREIGN KEY (targetid) REFERENCES targets(targetid) ON DELETE CASCADE;


--
-- Name: jobs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: jobs_job_state_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_job_state_id_fkey FOREIGN KEY (job_state_id) REFERENCES job_states(job_state_id) ON DELETE CASCADE;


--
-- Name: jobs_job_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_job_type_id_fkey FOREIGN KEY (job_type_id) REFERENCES job_types(job_type_id) ON DELETE CASCADE;


--
-- Name: jobs_rest_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_rest_method_id_fkey FOREIGN KEY (rest_method_id) REFERENCES rest_methods(rest_method_id) ON DELETE CASCADE;


--
-- Name: labels_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY labels
    ADD CONSTRAINT labels_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: latestcommit_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY latestcommit
    ADD CONSTRAINT latestcommit_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: membershiprequests_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY membershiprequests
    ADD CONSTRAINT membershiprequests_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: membershiprequests_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY membershiprequests
    ADD CONSTRAINT membershiprequests_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: outboundmirrors_sourceprojectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY outboundmirrors
    ADD CONSTRAINT outboundmirrors_sourceprojectid_fkey FOREIGN KEY (sourceprojectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: outboundmirrorsupdateservices_outboundmirrorid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY outboundmirrorsupdateservices
    ADD CONSTRAINT outboundmirrorsupdateservices_outboundmirrorid_fkey FOREIGN KEY (outboundmirrorid) REFERENCES outboundmirrors(outboundmirrorid) ON DELETE CASCADE;


--
-- Name: outboundmirrorsupdateservices_updateserviceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY outboundmirrorsupdateservices
    ADD CONSTRAINT outboundmirrorsupdateservices_updateserviceid_fkey FOREIGN KEY (updateserviceid) REFERENCES updateservices(updateserviceid) ON DELETE CASCADE;


--
-- Name: packageindex_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY packageindex
    ADD CONSTRAINT packageindex_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: pki_certificates_issuer_fingerprint_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY pki_certificates
    ADD CONSTRAINT pki_certificates_issuer_fingerprint_fkey FOREIGN KEY (issuer_fingerprint) REFERENCES pki_certificates(fingerprint) ON DELETE SET NULL;


--
-- Name: platforms_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY platforms
    ADD CONSTRAINT platforms_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE SET NULL;


--
-- Name: platformscontentsourcetypes_platformid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY platformscontentsourcetypes
    ADD CONSTRAINT platformscontentsourcetypes_platformid_fkey FOREIGN KEY (platformid) REFERENCES platforms(platformid) ON DELETE CASCADE;


--
-- Name: platformsourcedata_platformsourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY platformsourcedata
    ADD CONSTRAINT platformsourcedata_platformsourceid_fkey FOREIGN KEY (platformsourceid) REFERENCES platformsources(platformsourceid) ON DELETE CASCADE;


--
-- Name: platformsplatformsources_platformid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY platformsplatformsources
    ADD CONSTRAINT platformsplatformsources_platformid_fkey FOREIGN KEY (platformid) REFERENCES platforms(platformid) ON DELETE CASCADE;


--
-- Name: platformsplatformsources_platformsourceid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY platformsplatformsources
    ADD CONSTRAINT platformsplatformsources_platformsourceid_fkey FOREIGN KEY (platformsourceid) REFERENCES platformsources(platformsourceid) ON DELETE CASCADE;


--
-- Name: popularprojects_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY popularprojects
    ADD CONSTRAINT popularprojects_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: productversions_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY productversions
    ADD CONSTRAINT productversions_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: projects_creatorid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY projects
    ADD CONSTRAINT projects_creatorid_fkey FOREIGN KEY (creatorid) REFERENCES users(userid) ON DELETE SET NULL;


--
-- Name: projectusers_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY projectusers
    ADD CONSTRAINT projectusers_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: projectusers_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY projectusers
    ADD CONSTRAINT projectusers_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: publishedreleases_createdby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY publishedreleases
    ADD CONSTRAINT publishedreleases_createdby_fkey FOREIGN KEY (createdby) REFERENCES users(userid) ON DELETE SET NULL;


--
-- Name: publishedreleases_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY publishedreleases
    ADD CONSTRAINT publishedreleases_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: publishedreleases_publishedby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY publishedreleases
    ADD CONSTRAINT publishedreleases_publishedby_fkey FOREIGN KEY (publishedby) REFERENCES users(userid) ON DELETE SET NULL;


--
-- Name: publishedreleases_updatedby_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY publishedreleases
    ADD CONSTRAINT publishedreleases_updatedby_fkey FOREIGN KEY (updatedby) REFERENCES users(userid) ON DELETE SET NULL;


--
-- Name: querysets_queryset_children_from_queryset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_queryset_children
    ADD CONSTRAINT querysets_queryset_children_from_queryset_id_fkey FOREIGN KEY (from_queryset_id) REFERENCES querysets_queryset(query_set_id) ON DELETE CASCADE;


--
-- Name: querysets_queryset_children_to_queryset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_queryset_children
    ADD CONSTRAINT querysets_queryset_children_to_queryset_id_fkey FOREIGN KEY (to_queryset_id) REFERENCES querysets_queryset(query_set_id) ON DELETE CASCADE;


--
-- Name: querysets_queryset_filter_entries_filterentry_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_queryset_filter_entries
    ADD CONSTRAINT querysets_queryset_filter_entries_filterentry_id_fkey FOREIGN KEY (filterentry_id) REFERENCES querysets_filterentry(filter_entry_id) ON DELETE CASCADE;


--
-- Name: querysets_queryset_filter_entries_queryset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_queryset_filter_entries
    ADD CONSTRAINT querysets_queryset_filter_entries_queryset_id_fkey FOREIGN KEY (queryset_id) REFERENCES querysets_queryset(query_set_id) ON DELETE CASCADE;


--
-- Name: querysets_querytag_query_set_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_querytag
    ADD CONSTRAINT querysets_querytag_query_set_id_fkey FOREIGN KEY (query_set_id) REFERENCES querysets_queryset(query_set_id) ON DELETE CASCADE;


--
-- Name: querysets_systemtag_inclusion_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_systemtag
    ADD CONSTRAINT querysets_systemtag_inclusion_method_id_fkey FOREIGN KEY (inclusion_method_id) REFERENCES querysets_inclusionmethod(inclusion_method_id) ON DELETE CASCADE;


--
-- Name: querysets_systemtag_query_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_systemtag
    ADD CONSTRAINT querysets_systemtag_query_tag_id_fkey FOREIGN KEY (query_tag_id) REFERENCES querysets_querytag(query_tag_id) ON DELETE CASCADE;


--
-- Name: querysets_systemtag_system_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY querysets_systemtag
    ADD CONSTRAINT querysets_systemtag_system_id_fkey FOREIGN KEY (system_id) REFERENCES inventory_system(system_id) ON DELETE CASCADE;


--
-- Name: targetdata_targetid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY targetdata
    ADD CONSTRAINT targetdata_targetid_fkey FOREIGN KEY (targetid) REFERENCES targets(targetid) ON DELETE CASCADE;


--
-- Name: targetimagesdeployed_fileid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY targetimagesdeployed
    ADD CONSTRAINT targetimagesdeployed_fileid_fkey FOREIGN KEY (fileid) REFERENCES buildfiles(fileid) ON DELETE CASCADE;


--
-- Name: targetimagesdeployed_targetid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY targetimagesdeployed
    ADD CONSTRAINT targetimagesdeployed_targetid_fkey FOREIGN KEY (targetid) REFERENCES targets(targetid) ON DELETE CASCADE;


--
-- Name: targetusercredentials_targetcredentialsid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY targetusercredentials
    ADD CONSTRAINT targetusercredentials_targetcredentialsid_fkey FOREIGN KEY (targetcredentialsid) REFERENCES targetcredentials(targetcredentialsid) ON DELETE CASCADE;


--
-- Name: targetusercredentials_targetid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY targetusercredentials
    ADD CONSTRAINT targetusercredentials_targetid_fkey FOREIGN KEY (targetid) REFERENCES targets(targetid) ON DELETE CASCADE;


--
-- Name: targetusercredentials_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY targetusercredentials
    ADD CONSTRAINT targetusercredentials_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: topprojects_projectid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY topprojects
    ADD CONSTRAINT topprojects_projectid_fkey FOREIGN KEY (projectid) REFERENCES projects(projectid) ON DELETE CASCADE;


--
-- Name: urldownloads_urlid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY urldownloads
    ADD CONSTRAINT urldownloads_urlid_fkey FOREIGN KEY (urlid) REFERENCES filesurls(urlid) ON DELETE CASCADE;


--
-- Name: userdata_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY userdata
    ADD CONSTRAINT userdata_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: usergroupmembers_usergroupid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY usergroupmembers
    ADD CONSTRAINT usergroupmembers_usergroupid_fkey FOREIGN KEY (usergroupid) REFERENCES usergroups(usergroupid) ON DELETE CASCADE;


--
-- Name: usergroupmembers_userid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: conary
--

ALTER TABLE ONLY usergroupmembers
    ADD CONSTRAINT usergroupmembers_userid_fkey FOREIGN KEY (userid) REFERENCES users(userid) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: conary
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM conary;
GRANT ALL ON SCHEMA public TO conary;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

-- Generated on 2011-10-05 13:38:32 -0400 from revision cb0c5da911c6
