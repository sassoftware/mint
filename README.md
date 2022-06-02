# SAS App Engine Mint -- Archived Repository
**Notice: This repository is part of a Conary/rpath project at SAS that is no longer supported or maintained. Hence, the repository is being archived and will live in a read-only state moving forward. Issues, pull requests, and changes will no longer be accepted.**

Overview
--------

Mint is the central API for SAS App Engine. It consists of a number of components:

* REST API, backed by Django. This code is found in mint.django_rest
* Older "restlib" REST API, located in mint.rest. Mostly no longer required but
  is cross-linked from the Django API in a handful of places.
* XMLRPC API. Primarily used for starting image builds, and also internally
  used in many places. Located in mint.server
* Conary repository interface (mint.db.repository, mint.web.conaryhooks)
* Supporting scripts in scripts/ and mint.scripts - repository indexing, job
  cleanup, schema migrations, X509 management, mirroring inbound and outbound,
  etc.
* Credential store daemon - encrypts virtualization target credentials before
  storing in the database
* External auth daemon - Optionally checks user passwords against PAM
* System configuration and puppet scripts
