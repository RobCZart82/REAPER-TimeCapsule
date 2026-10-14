"""Atomic no-replace staging publication. Unsupported operations fail closed."""
import ctypes
import errno
import os
import sys


def publish_directory(source, destination):
    return _publish_exclusive(source, destination)


def publish_file(source, destination):
    """Native same-volume exclusive rename, including files on non-link volumes."""
    return _publish_exclusive(source, destination)


def _publish_exclusive(source, destination):
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
            raise FileExistsError(code, 'Publication destination already exists')
        raise OSError(code, 'Cannot safely publish staging; exclusive rename must be supported')


def require_path_capacity(parent, relatives):
    """Conservative capacity preflight; names are validated separately."""
    from pathlib import Path
    parent = Path(parent)
    if sys.platform == 'win32':
        # Restore I/O uses extended-length paths, so retain component safety
        # while allowing paths up to the Windows extended-length limit.
        component_limit, path_limit = 255, 32760
        units = lambda value: len(value.encode('utf-16-le')) // 2
    else:
        component_limit = os.pathconf(parent, 'PC_NAME_MAX')
        path_limit = os.pathconf(parent, 'PC_PATH_MAX') - 1
        units = lambda value: len(os.fsencode(value))
    for relative in relatives:
        path = parent / relative
        if (component_limit > 0 and any(units(part) > component_limit for part in path.parts)) or (
                path_limit > 0 and units(str(path)) > path_limit):
            raise ValueError('Recovery path exceeds conservative filesystem capacity; choose a shorter parent or portable-name recovery')
