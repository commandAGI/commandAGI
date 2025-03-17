from commandAGI.computers.base_computer.base_subprocess import BaseComputerSubprocess


class BaseApplication(BaseComputerSubprocess):
    """Base class for application operations.

    This class defines the interface for working with applications.
    Implementations should provide methods to control application windows,
    execute commands, and interact with application interfaces.
    """

