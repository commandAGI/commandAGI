import io
from pathlib import Path
from typing import Optional, TypeAlias, Union

from commandAGI.computers.base_computer import BaseComputer
from commandAGI.computers.base_computer.base_computer_file import \
    BaseComputerFile

LocalFile: TypeAlias = Union[io.TextIOWrapper, io.BufferedReader, io.BufferedWriter]

class LocalComputerFile(BaseComputerFile):
    """Implementation of BaseComputerFile for local computer files.

    This class provides a direct passthrough to the built-in file object for local files.
    No temporary files or copying is used - we directly access the file in its original location.
    """

    def __init__(
        self,
        computer: "BaseComputer",
        path: Union[str, Path],
        mode: str = "r",
        encoding: Optional[str] = None,
        errors: Optional[str] = None,
        buffering: int = -1,
    ):
        """Initialize a local computer file.

        For local files, we directly open the file in its original location.

        Args:
            computer: The computer instance this file belongs to
            path: Path to the file on the computer
            mode: File mode ('r', 'w', 'a', 'rb', 'wb', etc.)
            encoding: Text encoding to use (for text modes)
            errors: How to handle encoding/decoding errors
            buffering: Buffering policy (-1 for default)
        """Path
        # Store basic attributes
        self.computer = computer
        self.path = Path(path)
        self.mode = mode

        # Open the file directly
        kwargs = {}
        if encoding is not None and "b" not in mode:
            kwargs["encoding"] = encoding
        if errors is not None:
            kwargs["errors"] = errors
        if buffering != -1:
            kwargs["buffering"] = buffering

        # Just open the file directly - let the built-in open() handle all
        # errors
        self._file = open(path, mode, **kwargs)
        self._closed = False

    # Override base class methods to do nothing
    def _setup_temp_file(self):
        pass

    def _copy_from_computer(self):
        pass

    def _copy_to_computer(self):
        pass

    def _open_temp_file(self):
        pass

    # Delegate all file operations directly to the underlying file object
    def read(self, size=None):
        return self._file.read() if size is None else self._file.read(size)

    def write(self, data):
        return self._file.write(data)

    def seek(self, offset, whence=0):
        return self._file.seek(offset, whence)

    def tell(self):
        return self._file.tell()

    def flush(self):
        self._file.flush()

    def close(self):
        if not self._closed:
            self._file.close()
            self._closed = True

    def readable(self):
        return self._file.readable()

    def writable(self):
        return self._file.writable()

    def seekable(self):
        return self._file.seekable()

    def readline(self, size=-1):
        return self._file.readline(size)

    def readlines(self, hint=-1):
        return self._file.readlines(hint)

    def writelines(self, lines):
        self._file.writelines(lines)

    def __iter__(self):
        return self._file.__iter__()

    def __next__(self):
        return self._file.__next__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
