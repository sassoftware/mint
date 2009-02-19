#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, const char* argv[])
{
   setuid(0);
   return system("/sbin/service httpd graceful");
}

