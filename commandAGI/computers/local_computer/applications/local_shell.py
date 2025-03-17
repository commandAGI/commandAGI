from commandAGI.computers.base_computer.applications.base_shell import BaseShell
from commandAGI.computers.local_computer.local_subprocess import LocalSubprocess, LocalApplication


class LocalShell(BaseShell, LocalApplication):
    """Local class for shell operations.

    This class defines the interface for working with command-line shells.
    Implementations should provide methods to execute commands and interact
    with the shell through standard input/output streams.
    """

    _process: Optional[subprocess.Popen] = None
    _master_fd: Optional[int] = None
    _slave_fd: Optional[int] = None
    _output_buffer: str = ""
    _lock: threading.Lock = threading.Lock()

    def __init__(
        self,
        executable: str = DEFAULT_SHELL_EXECUTIBLE,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize a LocalShell instance.

        Args:
            executable: Path to the shell executable
            cwd: Initial working directory
            env: Environment variables to set
            logger: Logger instance
        """
        super().__init__(
            executable=executable,
            cwd=Path(cwd) if cwd else Path.cwd(),
            env=env or {},
            logger=logger or logging.getLogger("commandAGI.shell"),
        )
        self._lock = threading.Lock()

    def start(self) -> bool:
        """Start the shell process.

        Returns:
            bool: True if the shell was started successfully, False otherwise.
        """
        if self.is_running():
            self._logger.info("Shell is already running")
            return True

        try:
            self._logger.info(
                f"Starting shell with executable: {
                    self.executable}"
            )

            # Set up environment
            env = os.environ.copy()
            if self.env:
                env.update(self.env)

            if platform.system() == "Windows":
                # Windows implementation using subprocess with pipes
                self._process = subprocess.Popen(
                    # Use cmd.exe as the shell
                    ["cmd.exe", "/c", self.executable],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.cwd,
                    env=env,
                    shell=False,  # Don't create another shell layer
                    text=True,
                    bufsize=0,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # New process group
                )
                self.pid = self._process.pid
            else:
                # Unix implementation using pty
                self._master_fd, self._slave_fd = pty.openpty()
                # Make the master file descriptor non-blocking
                flags = fcntl.fcntl(self._master_fd, fcntl.F_GETFL)
                fcntl.fcntl(self._master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                # Start the shell process
                self._process = subprocess.Popen(
                    [self.executable],
                    stdin=self._slave_fd,
                    stdout=self._slave_fd,
                    stderr=self._slave_fd,
                    cwd=self.cwd,
                    env=env,
                    preexec_fn=os.setsid,  # Create new session
                )
                self.pid = self._process.pid

            self._logger.info(f"Shell started with PID: {self.pid}")

            # Change to the initial working directory if specified
            if self.cwd:
                self.change_directory(self.cwd)

            return True
        except Exception as e:
            self._logger.error(f"Error starting shell: {e}")
            self._cleanup()
            return False

    def stop(self) -> bool:
        """Stop the shell process.

        Returns:
            bool: True if the shell was stopped successfully, False otherwise.
        """
        if not self.is_running():
            self._logger.info("Shell is not running")
            return True

        try:
            self._logger.info(f"Stopping shell with PID: {self.pid}")

            if platform.system() == "Windows":
                # Send exit command to gracefully exit
                self.execute("exit", timeout=1)

                # If still running, terminate
                if self._process and self._process.poll() is None:
                    self._process.terminate()
                    self._process.wait(timeout=3)
            else:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(self.pid), signal.SIGTERM)

                # Wait for the process to terminate
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # If still running, send SIGKILL
                    os.killpg(os.getpgid(self.pid), signal.SIGKILL)

            self._cleanup()
            self._logger.info("Shell stopped")
            return True
        except Exception as e:
            self._logger.error(f"Error stopping shell: {e}")
            self._cleanup()
            return False

    def _cleanup(self):
        """Clean up resources."""
        if platform.system() != "Windows" and self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

        if platform.system() != "Windows" and self._slave_fd is not None:
            try:
                os.close(self._slave_fd)
            except OSError:
                pass
            self._slave_fd = None

        self._process = None
        self.pid = None

    def execute(self, command: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute a command in the shell and return the result.

        Args:
            command: The command to execute
            timeout: Optional timeout in seconds

        Returns:
            Dict containing stdout, stderr, and return code
        """
        if not self.is_running():
            self.start()

        try:
            self._logger.debug(f"Executing command: {command}")

            # Clear the output buffer before sending the command
            with self._lock:
                self._output_buffer = ""

            # Send the command with a newline
            self.send_input(command + "\n")

            # Read the output
            start_time = time.time()
            output = ""

            # Wait for the command to complete
            while timeout is None or (time.time() - start_time) < timeout:
                new_output = self.read_output(timeout=0.1)
                if new_output:
                    output += new_output

                # Check if the command has completed (prompt is shown)
                if output and (output.endswith("$ ") or output.endswith("> ")):
                    break

                time.sleep(0.1)

            # Remove the command from the output
            lines = output.splitlines()
            if lines and command in lines[0]:
                output = "\n".join(lines[1:])

            return {
                "stdout": output,
                "stderr": "",  # We can't separate stdout and stderr with pty
                "returncode": 0,  # We can't easily get the return code
            }
        except Exception as e:
            self._logger.error(f"Error executing command: {e}")
            return {"stdout": "", "stderr": str(e), "returncode": 1}

    def read_output(self, timeout: Optional[float] = None) -> str:
        """Read any available output from the shell.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            str: The output from the shell
        """
        if not self.is_running():
            return ""

        with self._lock:
            if platform.system() == "Windows":
                # Windows implementation
                if not self._process:
                    return ""

                output = ""
                try:
                    # Use a non-blocking read approach for Windows
                    if self._process.stdout.readable():
                        # Read available output without blocking
                        while msvcrt.kbhit():
                            char = self._process.stdout.read(1)
                            if not char:
                                break
                            output += char
                except Exception as e:
                    self._logger.error(f"Error reading output: {e}")

                self._output_buffer += output
                return output
            else:
                # Unix implementation using pty
                if self._master_fd is None:
                    return ""

                # Check if there's any output available
                if timeout is not None:
                    ready_to_read, _, _ = select.select(
                        [self._master_fd], [], [], timeout
                    )
                    if not ready_to_read:
                        return ""

                # Read output
                output = ""
                try:
                    while True:
                        data = os.read(self._master_fd, 1024)
                        if not data:
                            break
                        output += data.decode("utf-8", errors="replace")
                except (OSError, IOError):
                    pass

                self._output_buffer += output
                return output

    def send_input(self, text: str) -> bool:
        """Send input to the shell.

        Args:
            text: The text to send to the shell

        Returns:
            bool: True if the input was sent successfully, False otherwise
        """
        if not self.is_running():
            self.start()

        try:
            if platform.system() == "Windows":
                # Windows implementation
                if not self._process or not self._process.stdin:
                    return False

                self._process.stdin.write(text)
                self._process.stdin.flush()
            else:
                # Unix implementation using pty
                if self._master_fd is None:
                    return False

                os.write(self._master_fd, text.encode("utf-8"))

            return True
        except Exception as e:
            self._logger.error(f"Error sending input: {e}")
            return False

    def change_directory(self, path: Union[str, Path]) -> bool:
        """Change the current working directory of the shell.

        Args:
            path: The path to change to

        Returns:
            bool: True if the directory was changed successfully, False otherwise
        """
        path_str = str(path)
        result = self.execute(f"cd {shlex.quote(path_str)}")

        # Update the internal cwd if the command was successful
        if result["returncode"] == 0:
            self.cwd = Path(path_str).resolve()
            return True
        return False

    def set_envvar(self, name: str, value: str) -> bool:
        """Set an environment variable in the shell.

        Args:
            name: The name of the environment variable
            value: The value to set

        Returns:
            bool: True if the variable was set successfully, False otherwise
        """
        if platform.system() == "Windows":
            cmd = f"set {name}={value}"
        else:
            cmd = f"export {name}={shlex.quote(value)}"

        result = self.execute(cmd)

        # Update the internal env if the command was successful
        if result["returncode"] == 0:
            self.env[name] = value
            return True
        return False

    def get_envvar(self, name: str) -> Optional[str]:
        """Get the value of an environment variable from the shell.

        Args:
            name: The name of the environment variable

        Returns:
            Optional[str]: The value of the environment variable, or None if it doesn't exist
        """
        if platform.system() == "Windows":
            cmd = f"echo %{name}%"
        else:
            cmd = f"echo ${name}"

        result = self.execute(cmd)

        if result["returncode"] == 0 and result["stdout"].strip():
            value = result["stdout"].strip()
            # If the variable doesn't exist, Windows will return the original
            # string
            if platform.system() == "Windows" and value == f"%{name}%":
                return None
            return value
        return None

    def is_running(self) -> bool:
        """Check if the shell process is running.

        Returns:
            bool: True if the shell is running, False otherwise
        """
        if self._process is None or self.pid is None:
            return False

        # Check if the process is still running
        try:
            if platform.system() == "Windows":
                return self._process.poll() is None
            else:
                # Check if the process exists
                os.kill(self.pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False

    @property
    def current_directory(self) -> Path:
        """Get the current working directory of the shell.

        Returns:
            Path: The current working directory
        """
        if platform.system() == "Windows":
            cmd = "cd"
        else:
            cmd = "pwd"

        result = self.execute(cmd)

        if result["returncode"] == 0 and result["stdout"].strip():
            return Path(result["stdout"].strip())
        return self.cwd  # Fall back to the stored cwd
