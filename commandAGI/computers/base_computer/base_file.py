
class BaseComputerFile(FileIO, ABC):
    """Base class for computer-specific file implementations.

    This class provides a file-like interface for working with files on remote computers.
    It mimics the built-in file object API to allow for familiar usage patterns.

    The implementation copies the file from the computer to a local temporary directory,
    performs operations on the local copy, and syncs changes back to the computer
    when flushing or closing the file.
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
        # Store basic attributes
        self.computer = computer
        self.path = Path(path)
        self.mode = mode
        self._closed = False
        self._modified = False

        # Create a unique filename in the temp directory
        import os

        temp_filename = f"{hash(str(self.path))}-{os.path.basename(self.path)}"
        self._temp_path = Path(self.computer.temp_dir) / temp_filename

        # Copy from remote to local temp file if needed
        if "r" in mode or "a" in mode or "+" in mode:
            try:
                if self.path.exists():
                    self.computer._copy_from_computer(self.path, self._temp_path)
            except Exception as e:
                if "r" in mode and not ("+" in mode or "a" in mode or "w" in mode):
                    # If we're only reading, this is an error
                    raise IOError(f"Could not copy file from computer: {e}")
                # Otherwise, we'll create a new file

        # Open the file
        kwargs = {}
        if encoding is not None and "b" not in mode:
            kwargs["encoding"] = encoding
        if errors is not None:
            kwargs["errors"] = errors
        if buffering != -1:
            kwargs["buffering"] = buffering

        self._file = open(self._temp_path, mode, **kwargs)

    def read(self, size=None):
        """Read from the file."""
        return self._file.read() if size is None else self._file.read(size)

    def write(self, data):
        """Write to the file."""
        self._modified = True
        return self._file.write(data)

    def seek(self, offset, whence=0):
        """Change the stream position."""
        return self._file.seek(offset, whence)

    def tell(self):
        """Return the current stream position."""
        return self._file.tell()

    def flush(self):
        """Flush the write buffers and sync changes back to the computer."""
        self._file.flush()
        if self.writable() and self._modified:
            try:
                # Ensure the directory exists
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.computer._copy_to_computer(self._temp_path, self.path)
                self._modified = False
            except Exception as e:
                raise IOError(f"Could not copy file to computer: {e}")

    def close(self):
        """Close the file and sync changes back to the computer."""
        if not self._closed:
            self.flush()
            self._file.close()
            self._closed = True

    def readable(self):
        """Return True if the file can be read."""
        return self._file.readable()

    def writable(self):
        """Return True if the file can be written."""
        return self._file.writable()

    def seekable(self):
        """Return True if the file supports random access."""
        return self._file.seekable()

    def readline(self, size=-1):
        """Read until newline or EOF."""
        return self._file.readline(size)

    def readlines(self, hint=-1):
        """Read until EOF using readline() and return a list of lines."""
        return self._file.readlines(hint)

    def writelines(self, lines):
        """Write a list of lines to the file."""
        self._modified = True
        self._file.writelines(lines)

    def __iter__(self):
        """Return an iterator over the file's lines."""
        return self._file.__iter__()

    def __next__(self):
        """Return the next line from the file."""
        return self._file.__next__()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
