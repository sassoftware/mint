/* Copyright (C) 2006 rPath, Inc.
 * All rights reserved.
 */

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <libgen.h>

/* Program version */
#define VER                 "0.1"

#define CID_NOPARENT        0x0
#define SPARSE_MAGICNUMBER  0x564d444b /* 'V' 'M' 'D' 'K' */
#define VERSION             0x1
#define FLAGS               0x3
#define SELC                '\n'
#define NELC                ' '
#define DELC1               '\r'
#define DELC2               '\n'
#define GRAINSIZE           0x00010000 /*bytes in a grain*/
#define GRAINSECTORS        0x00000080 /*sectors in a grain*/

/* 512 Grain Tables Per Grain Table Entry*/
#define GTEPERGT            0x00000200
#define SECTORSIZE          0x00000200 /* 512 Bytes per sector */

/* Conversion macros */
#define BYTES(x)    ((x)<<9)
#define SECTORS(x)    ((x)>>9)

typedef u_int64_t  SectorType;
typedef u_int8_t   Bool;

typedef struct SparseExtentHeader {
    u_int32_t   magicNumber;        /* VMDK */
    u_int32_t   version;            /* 1 */
    u_int32_t   flags;              /* 3 */
    SectorType  capacity;           /* Size of the extent */
    SectorType  grainSize;          /* 128 */
    SectorType  descriptorOffset;   /* 1 */
    SectorType  descriptorSize;     /* 20, can this be smaller? */
    u_int32_t   numGTEsPerGT;       /* 512 */
    SectorType  rgdOffset;          /* 21 */
    SectorType  gdOffset;           /* depends on how many GTEs per GT and
                                     * the total size of the extent
                                     */
    SectorType  overHead;           /* 256 or so */
    Bool        uncleanShutdown;    /* False */
    char        singleEndLineChar;  /* SELC */
    char        nonEndLineChar;     /* NELC */
    char        doubleEndLineChar1; /* DELC1 */
    char        doubleEndLineChar2; /* DELC2 */
    u_int8_t    pad[435];
} SparseExtentHeader;

int numGTs(int outsize) {
    int numgrains = ceil((double)outsize / GRAINSIZE);
    return ceil((double)numgrains / GTEPERGT);
}

int GT0Offset(size_t numgts) {
    return ceil((double)(numgts * 4) / SECTORSIZE);
}

void SparseExtentHeader_init(SparseExtentHeader *hd, u_int32_t outsize) {
    memset(hd, 0, sizeof(SparseExtentHeader));
    size_t numgts = numGTs(outsize);
    size_t gt0offset = GT0Offset(numgts);
    hd->magicNumber =       SPARSE_MAGICNUMBER;
    hd->version =           VERSION;
    hd->flags =             FLAGS;
    hd->capacity =          SECTORS(outsize);
    hd->grainSize =         SECTORS(GRAINSIZE);
    hd->descriptorOffset =  1;
    hd->descriptorSize   =  20;
    hd->numGTEsPerGT =      GTEPERGT;
    hd->rgdOffset =         hd->descriptorSize + hd->descriptorOffset;

    /*offset of the first GT + total number of GTs * 4 sectors per GT */
    u_int32_t metadatasize =      gt0offset + numgts*4;
    hd->gdOffset  =         hd->rgdOffset + metadatasize;
    /* The overHead is grain aligned */
    hd->overHead =          ((2 * metadatasize / hd->grainSize) +
                            (((2 * metadatasize) % hd->grainSize) ? 1: 0)) *
                            hd->grainSize;
    hd->uncleanShutdown =   0;
    hd->singleEndLineChar = SELC;
    hd->nonEndLineChar =    NELC;
    hd->doubleEndLineChar1= DELC1;
    hd->doubleEndLineChar2= DELC2;
}

int writeDescriptorFile(FILE * of, const u_int32_t outsize,
                        const char * outfile,
                        const u_int32_t cylinders,
                        const u_int8_t heads,
                        const u_int8_t sectors) {
    size_t len = strlen(outfile);
    char * cpoutfile = (char*)malloc(sizeof(char)*(len + 1));
    strncpy(cpoutfile, outfile, strlen(outfile));
    cpoutfile[len] = '\0';
    int returner = 0;
    returner += fprintf(of, "# Disk DescriptorFile\n"
        "version=1\n"
        "CID=fffffffe\n"
        "parentCID=ffffffff\n");
    returner += fprintf(of, "createType=\"monolithicSparse\"\n"
        "\n"
        "# Extent description\n"
        "RW %d SPARSE \"%s\"\n", SECTORS(outsize), basename(cpoutfile));

    returner += fprintf(of, "\n"
        "# The Disk Data Base \n"
        "#DDB\n\n"
        "ddb.virtualHWVersion = \"3\"\n"
        "ddb.geometry.cylinders = \"%d\"\n"
        "ddb.geometry.heads = \"%d\"\n"
        "ddb.geometry.sectors = \"%d\"\n"
        "ddb.adapterType = \"ide\"\n", cylinders, heads, sectors);

    free(cpoutfile);
    return returner;
}

int writeGrainDirectory(const size_t offset, const size_t outsize, FILE * of) {
    size_t returner = 0;
    size_t i;
    size_t stop = numGTs(outsize);
    size_t start = offset + GT0Offset(stop);
    size_t cur;
    for (i=0; i < stop; i++) {
        /* The next GT pointed to by a GDE is 4 sectors away  */
        cur = start + (i * 4);
        returner += fwrite((void*)&cur, sizeof(cur), 1, of);
    }
    return returner * sizeof(cur);
}

int writeGrainTables(const size_t offset, const size_t outsize, FILE * of) {
    size_t returner = 0;
    size_t i, numGrains = outsize / GRAINSIZE;
    size_t grainSize = SECTORS(GRAINSIZE);
    size_t cur;
    for (i = 0; i < numGrains; i++) {
        /* The next Grain is SECTORS(GRAINSIZE) away */
        cur = offset + (i * grainSize);
        returner += fwrite((void*)&cur, sizeof(cur), 1, of);
    }
    return returner * sizeof(cur);
}

int writeGrainTableData(const SparseExtentHeader * header, u_int32_t * grainTable, const size_t numgte, FILE * fd)
{
    size_t numgts = numGTs(BYTES(header->capacity));
    size_t gt0offset = GT0Offset(numgts);
    int returner = 0;
    //Seek to the first offset, and dump
    fseek(fd, BYTES(header->rgdOffset + gt0offset), SEEK_SET);
    returner += fwrite((void*)grainTable, sizeof(u_int32_t), numgte, fd);

    fseek(fd, BYTES(header->gdOffset + gt0offset), SEEK_SET);
    returner += fwrite((void*)grainTable, sizeof(u_int32_t), numgte, fd);
    return returner;
}

int copyData(const char* infile, const size_t outsize,
             const SparseExtentHeader * header, FILE * of) {
    FILE * in = fopen(infile, "rb");
    /* Always have 512 entries per grain table */
    u_int32_t limit = numGTs(outsize) * 512;
    u_int32_t * grainTable = (u_int32_t*)malloc(limit * sizeof(u_int32_t));
    memset((void*)grainTable, 0, limit * sizeof(u_int32_t));
    u_int32_t returner = 0, currentSector = header->overHead;
    u_int32_t pos = 0;
    u_int64_t zero = 0L;
    u_int8_t buf[65536];
    size_t read;
    while((read = fread((void*)&buf, sizeof(u_int8_t), 65536, in))) {
        /* Check to make sure it's not all zeros */
        int i, rem, stop;
        Bool blank = 1;
        rem = read % sizeof(u_int64_t);
        stop = read - rem;
        for(i=0; i < stop; i+=8)
        {
            //Check one u_int64_t at a time
            //memcmp
            if (memcmp(&buf[i], &zero, sizeof(u_int64_t))){
                blank = 0;
                break;
            }
        }
        if(blank && rem){
            if(memcmp(&buf[i], &zero, rem)) {
                blank = 0;
            }
        }

        //Finally, if it's not blank, write it, and add an entry in the grainTable
        if(!blank) {
            grainTable[pos] = currentSector;
            currentSector += GRAINSECTORS;
            returner += fwrite((void*)&buf, sizeof(u_int8_t), read, of);
        }
        pos++;
    }
    fclose(in);
    /* Write the grainTable to the two offsets */
    writeGrainTableData(header, grainTable, limit, of);
    free(grainTable);
    return returner * sizeof(u_int8_t);
}


static void usage(char * name)
{
    printf("%s - Version %s\n", name, VER);
    printf("%s -C cylinders [-H heads] [-S sectors] infile.img outfile.vmdk\n\n"
            "-C  Number of cylinders in infile.img\n"
            "-H  Number of heads in infile.img\n"
            "-S  Number of sectors in infile.img\n"
            "infile.img    RAW disk image\n"
            "outfile.vmdk  VMware virtual disk\n\n",
            name);
}

int zeropad(off_t numbytes, FILE * file)
{
    off_t i;
    for( i = 0; i < numbytes; i++) {
        fputc(0, file);
    }
    return i;
}

int main(int argc, char ** argv) {
    struct stat istat;
    SparseExtentHeader header;
    int c;
    u_int8_t heads = 0x10, sectors = 0x3f;
    u_int32_t cylinders = 0x0;

    // Parse command line options
    do {
        c = getopt(argc, argv, "C:H:S:");
        switch (c) {
            case 'C': cylinders = atoi(optarg); break;
            case 'H': heads = atoi(optarg); break;
            case 'S': sectors = atoi(optarg); break;
        }
    } while (c >= 0);

    if (cylinders == 0 || (argc - optind != 2)) {
        usage(argv[0]);
        return -1;
    }
    char * infile = argv[optind];
    char * outfile = argv[optind+1];

    // Figure out how big the extent needs to be
    int ret = stat(infile, &istat);
    if (ret) return errno;
    off_t padding = SECTORSIZE - (istat.st_size % SECTORSIZE);
    off_t outsize = istat.st_size + (padding == SECTORSIZE ? 0: padding);

    SparseExtentHeader_init(&header, outsize);

    FILE * of = fopen(outfile, "wb");
    if(of) {
        // Write the header
        fwrite((void*)&header, sizeof(SparseExtentHeader), 1, of);
        // Write the descriptor
        zeropad(BYTES(header.descriptorSize) - writeDescriptorFile(of, outsize, outfile, cylinders, heads, sectors), of);
        // Write the rGDE
        size_t sizeofGDE = GT0Offset(numGTs(outsize));
        zeropad( BYTES(sizeofGDE) - writeGrainDirectory(header.rgdOffset, outsize, of), of);
        // Write the rGTs
        zeropad( BYTES(numGTs(outsize) * 4) - writeGrainTables(header.overHead, outsize, of), of);
        // Write the GDE
        zeropad( BYTES(sizeofGDE) - writeGrainDirectory(header.gdOffset, outsize, of), of);
        // Write the GTs
        zeropad( BYTES(numGTs(outsize) * 4) - writeGrainTables(header.overHead, outsize, of), of);
        // Align to grain
        off_t pos;
        pos = ftello(of);
        padding = GRAINSIZE - (pos % GRAINSIZE);
        zeropad((padding == GRAINSIZE ? 0: padding), of);
        // Write the grains
        copyData(infile, outsize, &header, of);
    }
    fclose(of);
    return 0;
}

