/*
 * Copyright (c) 2006 rPath, Inc.
 *
 * All rights reserved.
 *
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <unistd.h>

#define PRINTF(...)
/* #define PRINTF(...) fprintf(stderr, __VA_ARGS__) */

#define GET_REAL(name) \
    PRINTF("[wrp %5d] %s\n", getpid(), #name); \
    if (!real_##name) real_##name = dlsym(RTLD_NEXT, #name);

#define RET \
    if (!ret) make_root(buf); \
    return ret;

#define RET64 \
    if (!ret) make_root64(buf); \
    return ret;



static void make_root(struct stat *s) {
    s->st_uid = 0;
    s->st_gid = 0;
}
static void make_root64(struct stat64 *s) {
    s->st_uid = 0;
    s->st_gid = 0;
}


int stat(const char *pathname, struct stat *buf) {
    static int (*real_stat)(const char *pathname, struct stat *buf) = NULL;
    int ret;

    GET_REAL(stat);
    ret = real_stat(pathname, buf);
    RET;
}

int stat64(const char *pathname, struct stat64 *buf) {
    static int (*real_stat64)(const char *pathname, struct stat64 *buf) = NULL;
    int ret;

    GET_REAL(stat64);
    ret = real_stat64(pathname, buf);
    RET64;
}

int lstat(const char *pathname, struct stat *buf) {
    static int (*real_lstat)(const char *pathname, struct stat *buf) = NULL;
    int ret;

    GET_REAL(lstat);
    ret = real_lstat(pathname, buf);
    RET;
}

int lstat64(const char *pathname, struct stat64 *buf) {
    static int (*real_lstat64)(const char *pathname, struct stat64 *buf) = NULL;
    int ret;

    GET_REAL(lstat64);
    ret = real_lstat64(pathname, buf);
    RET64;
}

int __xstat(int ver, const char *pathname, struct stat *buf) {
    static int (*real___xstat)(int ver, const char *pathname, struct stat *buf) = NULL;
    int ret;

    GET_REAL(__xstat);
    ret = real___xstat(ver, pathname, buf);
    RET;
}
    
int __xstat64(int ver, const char *pathname, struct stat64 *buf) {
    static int (*real___xstat64)(int ver, const char *pathname, struct stat64 *buf) = NULL;
    int ret;

    GET_REAL(__xstat64);
    ret = real___xstat64(ver, pathname, buf);
    RET64;
}

int __lxstat(int ver, const char *pathname, struct stat *buf) {
    static int (*real___lxstat)(int ver, const char *pathname, struct stat *buf) = NULL;
    int ret;

    GET_REAL(__lxstat);
    ret = real___lxstat(ver, pathname, buf);
    RET;
}

int __lxstat64(int ver, const char *pathname, struct stat64 *buf) {
    static int (*real___lxstat64)(int ver, const char *pathname, struct stat64 *buf) = NULL;
    int ret;

    GET_REAL(__lxstat64);
    ret = real___lxstat64(ver, pathname, buf);
    RET64;
}
