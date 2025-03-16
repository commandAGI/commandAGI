# TODO

[x] public observation methods should return real information, not a pydantic struct.
[x] public observation methods hsould also have property accessors
[x] screenshot should accept a format: Literal['base64', 'PIL', 'path']='PIL'
[x] add stubs: `pause`, `resume`, `start_stream`, `stop_stream`, `get_stream_url` stubs to the base computer
[x] add stubs: `upload` (client -> server), `download` (server -> client), `edit(filepath, contents, mode='create_or_replace', encoding)`
[x] add `@property sysinfo` and more stubs to the base computer (think of others)
[x] rename most of the action methods to somehting more user friendly. click -> click, execute_shell_command to shell
[x] make the computer.drag start coordinates optional
[x] rename daemoncomputer to computer
[o] ~~rename the repo to `command_computer`~~ No, its commandAGI
[x] make a decorator that i can  use to automatically annotate which methods should be picked up by fastapi and fastmcp. this decorator should be just for annotation purposes because its going to decorate methods
[x] get rid of teh tool properties since we now have a decorator that ectracts tols from a regular mehod
[ ] get rid of all the observation and action structs. just handle the raw properties
[ ] playright webbrowser, pupyteer webbrowser computer child/implementation classes
[ ] terminal
[x] get rid of all the bool returns
[x] preferred_video-Stream_mode; vnc|http
[ ] understand how i'm doing the run_process and shell and start/stop_shell and make it cleanand and unified. especially considering hte backend daemon that hosts acces to the remote processes
[ ] implement a start_vscode/cursor, start_texteditor, start_blender, start_onshape, start_kicad, start_ they all just spawn a process with a window (i need ta  way to get the window form a process)
[ ] get rid of local_pyautogui_computer, collapse local_pynput_computer into local_computer
[ ] use slash / and star * as appropriate in the pythonic api

Computer:
- processes: list[Process]
- running_processes: list[BaseComputerProcess] (these are managed by subprocess.Popen so we can feed/read them at any moment)
- start_process() -> RunningProcess
- shell(command, executible):
    1. create shell process
    2. execute the command
    3. get the result
    4. end the shell process
- _jupter_server_process
- _vscode_process
- _other_special_processes

Process(BaseModel)
- ..basic meta

RunningProcess(ProcessInfo)
- read
- write

File(BaseModel)