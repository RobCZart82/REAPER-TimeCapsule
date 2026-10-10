"""Atomic no-replace directory publication. Unsupported operations fail closed."""
import ctypes
import errno
import os
import sys


def publish_directory(source, destination):
    """Same-filesystem exclusive rename; never falls back to POSIX rename."""
    if sys.platform == 'win32':
        # Windows os.rename raises if the destination exists.
        os.rename(source, destination)
        return
    if sys.platform != 'darwin' and not sys.platform.startswith('linux'):
        raise OSError(errno.ENOTSUP, 'Exclusive restore publication unavailable on this platform')
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        function = getattr(libc, 'renamex_np', None)
        if function is None:
            raise OSError(errno.ENOTSUP, 'Exclusive restore publication unavailable')
        function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        result = function(os.fsencode(source), os.fsencode(destination), 0x4)  # RENAME_EXCL
    elif sys.platform.startswith('linux'):
        function = getattr(libc, 'renameat2', None)
        if function is None:
            raise OSError(errno.ENOTSUP, 'Exclusive restore publication unavailable')
        function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        result = function(-100, os.fsencode(source), -100, os.fsencode(destination), 1)  # NOREPLACE
    else:
        raise OSError(errno.ENOTSUP, 'Exclusive restore publication unavailable on this platform')
    if result != 0:
        code = ctypes.get_errno()
        if code in (errno.EEXIST, errno.ENOTEMPTY):
            raise FileExistsError(code, 'Restore destination already exists')
        raise OSError(code, 'Cannot safely publish restore; exclusive rename must be supported')
