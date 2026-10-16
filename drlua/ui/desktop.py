"""Windows installer coordination, independent of the view."""

import ctypes
from ctypes import wintypes


class ApplicationMutex:
    def __init__(self):
        create_mutex = ctypes.windll.kernel32.CreateMutexW
        create_mutex.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        create_mutex.restype = wintypes.HANDLE
        self.handle = create_mutex(None, False, "electblake.DrLua.Running")

    def close(self):
        close_handle = ctypes.windll.kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL
        close_handle(self.handle)
