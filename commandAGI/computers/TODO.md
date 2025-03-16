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
