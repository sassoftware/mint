r"""UUID objects (universally unique identifiers) according to RFC 4122.

This module provides immutable UUID objects (class UUID) and the functions
uuid1(), uuid3(), uuid4(), uuid5() for generating version 1, 3, 4, and 5
UUIDs as specified in RFC 4122.

If all you want is a unique ID, you should probably call uuid1() or uuid4().
Note that uuid1() may compromise privacy since it creates a UUID containing
the computer's network address.  uuid4() creates a random UUID.

Typical usage:

    >>> import uuid

    # make a UUID based on the host ID and current time
    >>> uuid.uuid1()
    UUID('a8098c1a-f86e-11da-bd1a-00112444be1e')

    # make a UUID using an MD5 hash of a namespace UUID and a name
    >>> uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
    UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e')

    # make a random UUID
    >>> uuid.uuid4()
    UUID('16fd2706-8baf-433b-82eb-8c7fada847da')

    # make a UUID using a SHA-1 hash of a namespace UUID and a name
    >>> uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
    UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')

    # make a UUID from a string of hex digits (braces and hyphens ignored)
    >>> x = uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e0f}')

    # convert a UUID to a string of hex digits in standard form
    >>> str(x)
    '00010203-0405-0607-0809-0a0b0c0d0e0f'

    # get the raw 16 bytes of the UUID
    >>> x.bytes
    '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f'

    # make a UUID from a 16-byte string
    >>> uuid.UUID(bytes=x.bytes)
    UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
"""

__author__ = 'Ka-Ping Yee <ping@zesty.ca>'

RESERVED_NCS, RFC_4122, RESERVED_MICROSOFT, RESERVED_FUTURE = [
    'reserved for NCS compatibility', 'specified in RFC 4122',
    'reserved for Microsoft compatibility', 'reserved for future definition']

class UUID(long):
    """Instances of the UUID class represent UUIDs as specified in RFC 4122.
    UUID objects are immutable, hashable, and usable as dictionary keys.
    Converting a UUID to a string with str() yields something in the form
    '12345678-1234-1234-1234-123456789abc'.  The UUID constructor accepts
    five possible forms: a similar string of hexadecimal digits, or a tuple
    of six integer fields (with 32-bit, 16-bit, 16-bit, 8-bit, 8-bit, and
    48-bit values respectively) as an argument named 'fields', or a string
    of 16 bytes (with all the integer fields in big-endian order) as an
    argument named 'bytes', or a string of 16 bytes (with the first three
    fields in little-endian order) as an argument named 'bytes_le', or a
    single 128-bit integer as an argument named 'int'.
    """
    __slots__ = ()

    def __new__(cls, hex=None, bytes=None, bytes_le=None, fields=None,
                       int=None, version=None):
        r"""Create a UUID from either a string of 32 hexadecimal digits,
        a string of 16 bytes as the 'bytes' argument, a string of 16 bytes
        in little-endian order as the 'bytes_le' argument, a tuple of six
        integers (32-bit time_low, 16-bit time_mid, 16-bit time_hi_version,
        8-bit clock_seq_hi_variant, 8-bit clock_seq_low, 48-bit node) as
        the 'fields' argument, or a single 128-bit integer as the 'int'
        argument.  When a string of hex digits is given, curly braces,
        hyphens, and a URN prefix are all optional.  For example, these
        expressions all yield the same UUID:

        UUID('{12345678-1234-5678-1234-567812345678}')
        UUID('12345678123456781234567812345678')
        UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
        UUID(bytes='\x12\x34\x56\x78'*4)
        UUID(bytes_le='\x78\x56\x34\x12\x34\x12\x78\x56' +
                      '\x12\x34\x56\x78\x12\x34\x56\x78')
        UUID(fields=(0x12345678, 0x1234, 0x5678, 0x12, 0x34, 0x567812345678))
        UUID(int=0x12345678123456781234567812345678)

        Exactly one of 'hex', 'bytes', 'bytes_le', 'fields', or 'int' must
        be given.  The 'version' argument is optional; if given, the resulting
        UUID will have its variant and version set according to RFC 4122,
        overriding the given 'hex', 'bytes', 'bytes_le', 'fields', or 'int'.
        """

        if [hex, bytes, bytes_le, fields, int].count(None) != 4:
            raise TypeError('need one of hex, bytes, bytes_le, fields, or int')
        if hex is not None:
            hex = hex.replace('urn:', '').replace('uuid:', '')
            hex = hex.strip('{}').replace('-', '')
            if len(hex) != 32:
                raise ValueError('badly formed hexadecimal UUID string')
            int = long(hex, 16)
        if bytes_le is not None:
            if len(bytes_le) != 16:
                raise ValueError('bytes_le is not a 16-char string')
            bytes = (bytes_le[3] + bytes_le[2] + bytes_le[1] + bytes_le[0] +
                     bytes_le[5] + bytes_le[4] + bytes_le[7] + bytes_le[6] +
                     bytes_le[8:])
        if bytes is not None:
            if len(bytes) != 16:
                raise ValueError('bytes is not a 16-char string')
            int = long(('%02x'*16) % tuple(map(ord, bytes)), 16)
        if fields is not None:
            if len(fields) != 6:
                raise ValueError('fields is not a 6-tuple')
            (time_low, time_mid, time_hi_version,
             clock_seq_hi_variant, clock_seq_low, node) = fields
            if not 0 <= time_low < 1<<32L:
                raise ValueError('field 1 out of range (need a 32-bit value)')
            if not 0 <= time_mid < 1<<16L:
                raise ValueError('field 2 out of range (need a 16-bit value)')
            if not 0 <= time_hi_version < 1<<16L:
                raise ValueError('field 3 out of range (need a 16-bit value)')
            if not 0 <= clock_seq_hi_variant < 1<<8L:
                raise ValueError('field 4 out of range (need an 8-bit value)')
            if not 0 <= clock_seq_low < 1<<8L:
                raise ValueError('field 5 out of range (need an 8-bit value)')
            if not 0 <= node < 1<<48L:
                raise ValueError('field 6 out of range (need a 48-bit value)')
            clock_seq = (clock_seq_hi_variant << 8L) | clock_seq_low
            int = ((time_low << 96L) | (time_mid << 80L) |
                   (time_hi_version << 64L) | (clock_seq << 48L) | node)
        if int is not None:
            if not 0 <= int < 1<<128L:
                raise ValueError('int is out of range (need a 128-bit value)')
        if version is not None:
            if not 1 <= version <= 5:
                raise ValueError('illegal version number')
            # Set the variant to RFC 4122.
            int &= ~(0xc000 << 48L)
            int |= 0x8000 << 48L
            # Set the version number.
            int &= ~(0xf000 << 64L)
            int |= version << 76L
        return long.__new__(cls, int)

    def __repr__(self):
        return 'UUID(%r)' % str(self)

    def __str__(self):
        hex = '%032x' % self
        return '%s-%s-%s-%s-%s' % (
            hex[:8], hex[8:12], hex[12:16], hex[16:20], hex[20:])

    @property
    def bytes(self):
        bytes = ''
        for shift in range(0, 128, 8):
            bytes = chr((self>> shift) & 0xff) + bytes
        return bytes

    @property
    def short(self):
        return str(self)[24:]


    def __copy__(self, memo=None):
        return self
    __deepcopy__ = __copy__

    def __getnewargs__(self):
        return None, None, None, None, long(self), None


def _find_mac(command, args, hw_identifiers, get_index):
    import os
    for dir in ['', '/sbin/', '/usr/sbin']:
        executable = os.path.join(dir, command)
        if not os.path.exists(executable):
            continue

        try:
            # LC_ALL to get English output, 2>/dev/null to
            # prevent output on stderr
            cmd = 'LC_ALL=C %s %s 2>/dev/null' % (executable, args)
            pipe = os.popen(cmd)
        except IOError:
            continue

        for line in pipe:
            words = line.lower().split()
            for i in range(len(words)):
                if words[i] in hw_identifiers:
                    return int(words[get_index(i)].replace(':', ''), 16)
    return None

def _ifconfig_getnode():
    """Get the hardware address on Unix by running ifconfig."""

    # This works on Linux ('' or '-a'), Tru64 ('-av'), but not all Unixes.
    for args in ('', '-a', '-av'):
        mac = _find_mac('ifconfig', args, ['hwaddr', 'ether'], lambda i: i+1)
        if mac:
            return mac

    import socket
    ip_addr = socket.gethostbyname(socket.gethostname())

    # Try getting the MAC addr from arp based on our IP address (Solaris).
    mac = _find_mac('arp', '-an', [ip_addr], lambda i: -1)
    if mac:
        return mac

    # This might work on HP-UX.
    mac = _find_mac('lanscan', '-ai', ['lan0'], lambda i: 0)
    if mac:
        return mac

    return None

def _ipconfig_getnode():
    """Get the hardware address on Windows by running ipconfig.exe."""
    import os, re
    dirs = ['', r'c:\windows\system32', r'c:\winnt\system32']
    try:
        import ctypes
        buffer = ctypes.create_string_buffer(300)
        ctypes.windll.kernel32.GetSystemDirectoryA(buffer, 300)
        dirs.insert(0, buffer.value.decode('mbcs'))
    except:
        pass
    for dir in dirs:
        try:
            pipe = os.popen(os.path.join(dir, 'ipconfig') + ' /all')
        except IOError:
            continue
        for line in pipe:
            value = line.split(':')[-1].strip().lower()
            if re.match('([0-9a-f][0-9a-f]-){5}[0-9a-f][0-9a-f]', value):
                return int(value.replace('-', ''), 16)

def _netbios_getnode():
    """Get the hardware address on Windows using NetBIOS calls.
    See http://support.microsoft.com/kb/118623 for details."""
    import win32wnet, netbios
    ncb = netbios.NCB()
    ncb.Command = netbios.NCBENUM
    ncb.Buffer = adapters = netbios.LANA_ENUM()
    adapters._pack()
    if win32wnet.Netbios(ncb) != 0:
        return
    adapters._unpack()
    for i in range(adapters.length):
        ncb.Reset()
        ncb.Command = netbios.NCBRESET
        ncb.Lana_num = ord(adapters.lana[i])
        if win32wnet.Netbios(ncb) != 0:
            continue
        ncb.Reset()
        ncb.Command = netbios.NCBASTAT
        ncb.Lana_num = ord(adapters.lana[i])
        ncb.Callname = '*'.ljust(16)
        ncb.Buffer = status = netbios.ADAPTER_STATUS()
        if win32wnet.Netbios(ncb) != 0:
            continue
        status._unpack()
        bytes = map(ord, status.adapter_address)
        return ((bytes[0]<<40L) + (bytes[1]<<32L) + (bytes[2]<<24L) +
                (bytes[3]<<16L) + (bytes[4]<<8L) + bytes[5])

# Thanks to Thomas Heller for ctypes and for his help with its use here.

# If ctypes is available, use it to find system routines for UUID generation.
_uuid_generate_random = _uuid_generate_time = _UuidCreate = None
try:
    import ctypes, ctypes.util

    # The uuid_generate_* routines are provided by libuuid on at least
    # Linux and FreeBSD, and provided by libc on Mac OS X.
    for libname in ['uuid', 'c']:
        try:
            lib = ctypes.CDLL(ctypes.util.find_library(libname))
        except:
            continue
        if hasattr(lib, 'uuid_generate_random'):
            _uuid_generate_random = lib.uuid_generate_random
        if hasattr(lib, 'uuid_generate_time'):
            _uuid_generate_time = lib.uuid_generate_time

    # On Windows prior to 2000, UuidCreate gives a UUID containing the
    # hardware address.  On Windows 2000 and later, UuidCreate makes a
    # random UUID and UuidCreateSequential gives a UUID containing the
    # hardware address.  These routines are provided by the RPC runtime.
    # NOTE:  at least on Tim's WinXP Pro SP2 desktop box, while the last
    # 6 bytes returned by UuidCreateSequential are fixed, they don't appear
    # to bear any relationship to the MAC address of any network device
    # on the box.
    try:
        lib = ctypes.windll.rpcrt4
    except:
        lib = None
    _UuidCreate = getattr(lib, 'UuidCreateSequential',
                          getattr(lib, 'UuidCreate', None))
except:
    pass

def _unixdll_getnode():
    """Get the hardware address on Unix using ctypes."""
    _buffer = ctypes.create_string_buffer(16)
    _uuid_generate_time(_buffer)
    return UUID(bytes=_buffer.raw).node

def _windll_getnode():
    """Get the hardware address on Windows using ctypes."""
    _buffer = ctypes.create_string_buffer(16)
    if _UuidCreate(_buffer) == 0:
        return UUID(bytes=_buffer.raw).node

def _random_getnode():
    """Get a random node ID, with eighth bit set as suggested by RFC 4122."""
    import random
    return random.randrange(0, 1<<48L) | 0x010000000000L

_node = None

def getnode():
    """Get the hardware address as a 48-bit positive integer.

    The first time this runs, it may launch a separate program, which could
    be quite slow.  If all attempts to obtain the hardware address fail, we
    choose a random 48-bit number with its eighth bit set to 1 as recommended
    in RFC 4122.
    """

    global _node
    if _node is not None:
        return _node

    import sys
    if sys.platform == 'win32':
        getters = [_windll_getnode, _netbios_getnode, _ipconfig_getnode]
    else:
        getters = [_unixdll_getnode, _ifconfig_getnode]

    for getter in getters + [_random_getnode]:
        try:
            _node = getter()
        except:
            continue
        if _node is not None:
            return _node

_last_timestamp = None

def uuid1(node=None, clock_seq=None):
    """Generate a UUID from a host ID, sequence number, and the current time.
    If 'node' is not given, getnode() is used to obtain the hardware
    address.  If 'clock_seq' is given, it is used as the sequence number;
    otherwise a random 14-bit sequence number is chosen."""

    # When the system provides a version-1 UUID generator, use it (but don't
    # use UuidCreate here because its UUIDs don't conform to RFC 4122).
    if _uuid_generate_time and node is clock_seq is None:
        _buffer = ctypes.create_string_buffer(16)
        _uuid_generate_time(_buffer)
        return UUID(bytes=_buffer.raw)

    global _last_timestamp
    import time
    nanoseconds = int(time.time() * 1e9)
    # 0x01b21dd213814000 is the number of 100-ns intervals between the
    # UUID epoch 1582-10-15 00:00:00 and the Unix epoch 1970-01-01 00:00:00.
    timestamp = int(nanoseconds/100) + 0x01b21dd213814000L
    if timestamp <= _last_timestamp:
        timestamp = _last_timestamp + 1
    _last_timestamp = timestamp
    if clock_seq is None:
        import random
        clock_seq = random.randrange(1<<14L) # instead of stable storage
    time_low = timestamp & 0xffffffffL
    time_mid = (timestamp >> 32L) & 0xffffL
    time_hi_version = (timestamp >> 48L) & 0x0fffL
    clock_seq_low = clock_seq & 0xffL
    clock_seq_hi_variant = (clock_seq >> 8L) & 0x3fL
    if node is None:
        node = getnode()
    return UUID(fields=(time_low, time_mid, time_hi_version,
                        clock_seq_hi_variant, clock_seq_low, node), version=1)

def uuid3(namespace, name):
    """Generate a UUID from the MD5 hash of a namespace UUID and a name."""
    try:
        from hashlib import md5
    except ImportError:
        from md5 import new as md5
    hash = md5(namespace.bytes + name).digest()
    return UUID(bytes=hash[:16], version=3)

def uuid4():
    """Generate a random UUID."""

    # When the system provides a version-4 UUID generator, use it.
    if _uuid_generate_random:
        _buffer = ctypes.create_string_buffer(16)
        _uuid_generate_random(_buffer)
        return UUID(bytes=_buffer.raw)

    # Otherwise, get randomness from urandom or the 'random' module.
    try:
        import os
        return UUID(bytes=os.urandom(16), version=4)
    except:
        import random
        bytes = [chr(random.randrange(256)) for i in range(16)]
        return UUID(bytes=bytes, version=4)

def uuid5(namespace, name):
    """Generate a UUID from the SHA-1 hash of a namespace UUID and a name."""
    try:
        from hashlib import sha1
    except ImportError:
        from sha import new as sha1
    hash = sha1(namespace.bytes + name).digest()
    return UUID(bytes=hash[:16], version=5)

# The following standard UUIDs are for use with uuid3() or uuid5().

NAMESPACE_DNS = UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_URL = UUID('6ba7b811-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_OID = UUID('6ba7b812-9dad-11d1-80b4-00c04fd430c8')
NAMESPACE_X500 = UUID('6ba7b814-9dad-11d1-80b4-00c04fd430c8')
