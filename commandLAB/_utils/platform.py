import platform

match platform.system():
    case "Windows":
        DEFAULT_SHELL_EXECUTIBLE = "cmd.exe"
    case "Linux":
        DEFAULT_SHELL_EXECUTIBLE = "/bin/bash"
    case "Darwin":
        DEFAULT_SHELL_EXECUTIBLE = "/bin/zsh"
